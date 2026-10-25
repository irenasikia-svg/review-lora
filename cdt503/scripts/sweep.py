"""CDT503 第 1 阶段：系统调参。以 v2 配置为基准，一次只改一个因素，依次训练并在验证集上评估。

基准：rank 16、学习率 1e-4、全部 28 层、batch 8、480 步、种子 42 —— 和 v2 完全相同，
所以基准组直接复制 v2 已有的检查点和日志（只读，不改动原文件），不重新训练。

每一组的流程：生成配置 → 训练（每 40 步存检查点、算验证损失）→ 选验证损失最低的检查点 → 在验证集上评估。
测试集不在这里用：选定最终配置后，单独跑一次 eval_split.py --split test。

断点续跑：每组的状态记在 cdt503/runs/<组名>/state.json。中途被打断后重新运行本脚本，
已完成的组会跳过；训练到一半的组从最近的检查点接着训。
  注意：mlx-lm 续跑时步数从 1 重新计数、检查点文件名也从头编号，会覆盖之前的文件，
  所以每次续跑写到一个新的"分段"目录 seg_<起始步>/，画曲线时再按起始步拼接。
  另外续跑时 Adam 优化器的动量会清零，日志里会记下续跑发生在第几步。

用法：
  uv run python cdt503/scripts/sweep.py --dry-run          # 只打印计划
  uv run python cdt503/scripts/sweep.py --smoke            # 冒烟测试：每组 10 步，结果写到 cdt503/results/smoke/
  uv run python cdt503/scripts/sweep.py                    # 正式跑全部
  uv run python cdt503/scripts/sweep.py --only rank4 lr2e-4
"""
import argparse
import datetime
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE_CONFIG = os.path.join(ROOT, "lora_config.yaml")
V2_ADAPTERS = os.path.join(ROOT, "adapters")
V2_LOG = os.path.join(ROOT, "logs/train.log")

# 组名 → 相对基准改了什么。一次只改一个因素
RUNS = {
    "baseline": {},
    "rank4": {"rank": 4},
    "rank8": {"rank": 8},
    "rank32": {"rank": 32},
    "lr5e-5": {"learning_rate": 5e-5},
    "lr2e-4": {"learning_rate": 2e-4},
    "layers8": {"num_layers": 8},
    "layers16": {"num_layers": 16},
    # 和基准完全一样，只换随机种子：用来估计"同一配置跑两次能差多少"，判断其他组的差异是不是噪声
    "baseline_seed43": {"seed": 43},
}
SMOKE = {"iters": 10, "steps_per_eval": 5, "save_every": 5, "steps_per_report": 5, "val_batches": 2}
SMOKE_EVAL_LIMIT = 16


class Paths:
    def __init__(self, name, smoke):
        kind = "smoke" if smoke else "sweep"
        self.name = name
        self.run = os.path.join(ROOT, f"cdt503/runs/{kind}/{name}")        # 权重（不入库）
        self.res = os.path.join(ROOT, f"cdt503/results/{kind}/{name}")     # 配置、日志、指标（入库）
        self.state = os.path.join(self.run, "state.json")
        self.sweep_log = os.path.join(ROOT, f"cdt503/results/{kind}/sweep.log")


def log(paths, msg):
    line = f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] {paths.name}: {msg}"
    print(line, flush=True)
    os.makedirs(os.path.dirname(paths.sweep_log), exist_ok=True)
    with open(paths.sweep_log, "a") as f:
        f.write(line + "\n")


def load_state(p):
    if os.path.exists(p.state):
        return json.load(open(p.state))
    return {"status": "pending", "segments": []}


def save_state(p, state):
    os.makedirs(p.run, exist_ok=True)
    tmp = p.state + ".tmp"
    json.dump(state, open(tmp, "w"), ensure_ascii=False, indent=2)
    os.replace(tmp, p.state)  # 原子替换：写到一半断电也不会留下坏文件


def make_config(name, overrides, smoke):
    cfg = yaml.safe_load(open(BASE_CONFIG))
    cfg["data"] = os.path.join(ROOT, "data/sft")
    for k, v in overrides.items():
        if k == "rank":
            cfg["lora_parameters"]["rank"] = v
        else:
            cfg[k] = v
    if smoke:
        cfg.update(SMOKE)
    return cfg


def checkpoints(state):
    """所有分段里已保存的检查点：{全局步数: 文件路径}"""
    found = {}
    for seg in state["segments"]:
        for f in glob.glob(os.path.join(seg["dir"], "*_adapters.safetensors")):
            local = int(os.path.basename(f).split("_")[0])
            found[seg["offset"] + local] = f
    return found


# —— 解析训练日志（新版 mlx-lm 的表格格式，先去掉终端颜色代码）——
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def parse_log(path):
    text = ANSI.sub("", open(path, errors="replace").read())
    train = [(int(i), float(v)) for i, v in re.findall(r"^\s*(\d+)\s+([\d.]+) [▼▲]", text, flags=re.M)]
    val = [(int(i), float(v)) for i, v in re.findall(r"^\s*(\d+)\s+val ([\d.]+)", text, flags=re.M)]
    m = re.search(r"Trainable parameters: ([\d.]+)% \(([\d.]+)M", text)
    params = {"trainable_pct": float(m.group(1)), "trainable_M": float(m.group(2))} if m else {}
    return train, val, params


def build_curves(state):
    """把各分段的日志拼成全局步数下的曲线。被打断那段里、最后一个检查点之后的记录属于丢掉的进度，去掉。"""
    segs = state["segments"]
    train, val, params = [], [], {}
    for i, seg in enumerate(segs):
        limit = segs[i + 1]["offset"] - seg["offset"] if i + 1 < len(segs) else float("inf")
        t, v, prm = parse_log(seg["log"])
        params = params or prm
        train += [(seg["offset"] + s, x) for s, x in t if s <= limit]
        # 续跑段第 1 步的验证损失和上一段最后一次重复，去掉
        val += [(seg["offset"] + s, x) for s, x in v if s <= limit and not (seg["offset"] and s == 1)]
    return sorted(train), sorted(val), params


def train(p, cfg, state, stop_after=None):
    """训练（或续跑）直到 cfg['iters'] 步。stop_after 仅用于测试续跑：存到该步检查点后强行结束进程。"""
    total = cfg["iters"]
    ckpts = checkpoints(state)
    done = max(ckpts, default=0)
    if done >= total:
        return True
    seg_dir = os.path.join(p.run, f"seg_{done}")
    if os.path.isdir(seg_dir):
        shutil.rmtree(seg_dir)  # 同一起点的上一次尝试没存下任何检查点，清掉重来
    seg_cfg = dict(cfg, adapter_path=seg_dir, iters=total - done)
    if done:
        seg_cfg["resume_adapter_file"] = ckpts[done]
        # 续跑时 Adam 动量清零，头几步会"一步跨太大"：冒烟测试里验证损失从 0.24 跳到 0.53。
        # 所以续跑段的学习率从 0 线性升到目标值（最多 20 步），之后保持不变。首次训练不加，和 v2 基准一致
        warmup = min(20, max(1, (total - done) // 2))
        seg_cfg["lr_schedule"] = {"name": "linear_schedule", "warmup": warmup,
                                  "arguments": [cfg["learning_rate"], cfg["learning_rate"], 1]}
        log(p, f"从第 {done} 步续跑（优化器动量清零，学习率预热 {warmup} 步）")
    os.makedirs(p.res, exist_ok=True)
    cfg_path = os.path.join(p.res, f"config_seg{done}.yaml")
    yaml.safe_dump(seg_cfg, open(cfg_path, "w"), allow_unicode=True, sort_keys=False)
    seg_log = os.path.join(p.res, f"train_seg{done}.log")
    state["segments"] = [s for s in state["segments"] if s["offset"] < done] + [
        {"offset": done, "dir": seg_dir, "log": seg_log, "started": time.time()}]
    state["status"] = "training"
    save_state(p, state)

    log(p, f"开始训练 第 {done + 1}–{total} 步，日志 {os.path.relpath(seg_log, ROOT)}")
    with open(seg_log, "w") as f:
        proc = subprocess.Popen([sys.executable, "-m", "mlx_lm", "lora", "-c", cfg_path],
                                stdout=f, stderr=subprocess.STDOUT, cwd=ROOT)
        while proc.poll() is None:
            time.sleep(5)
            if stop_after and done + max([int(os.path.basename(x).split("_")[0])
                                         for x in glob.glob(os.path.join(seg_dir, "*_adapters.safetensors"))],
                                        default=0) >= stop_after:
                proc.terminate()
                proc.wait()
                log(p, f"[测试] 在第 {stop_after} 步后模拟中断")
                return False
    state["segments"][-1]["ended"] = time.time()
    save_state(p, state)
    if proc.returncode != 0:
        log(p, f"训练进程异常退出（返回码 {proc.returncode}），见 {os.path.relpath(seg_log, ROOT)}")
        return False
    return max(checkpoints(state), default=0) >= total


def import_baseline(p, state):
    """基准组 = v2：复制检查点和日志，不重新训练。原文件只读。"""
    seg_dir = os.path.join(p.run, "seg_0")
    os.makedirs(seg_dir, exist_ok=True)
    for f in glob.glob(os.path.join(V2_ADAPTERS, "*")):
        shutil.copy2(f, seg_dir)
    os.makedirs(p.res, exist_ok=True)
    seg_log = os.path.join(p.res, "train_seg0.log")
    shutil.copy2(V2_LOG, seg_log)
    shutil.copy2(BASE_CONFIG, os.path.join(p.res, "config_seg0.yaml"))
    st = os.stat(V2_LOG)
    state["segments"] = [{"offset": 0, "dir": seg_dir, "log": seg_log,
                          "started": st.st_birthtime, "ended": st.st_mtime, "imported_from": "v2"}]
    log(p, "已从 v2 复制检查点和日志")


def finish(p, cfg, state, overrides, smoke):
    train_curve, val_curve, params = build_curves(state)
    ckpts = checkpoints(state)
    candidates = [(v, s) for s, v in val_curve if s in ckpts]
    best_val, best_step = min(candidates)
    best_dir = os.path.join(p.run, "best")
    os.makedirs(best_dir, exist_ok=True)
    shutil.copy2(os.path.join(state["segments"][0]["dir"], "adapter_config.json"), best_dir)
    shutil.copy2(ckpts[best_step], os.path.join(best_dir, "adapters.safetensors"))

    with open(os.path.join(p.res, "curve.json"), "w") as f:
        json.dump({"train": train_curve, "val": val_curve}, f)
    log(p, f"验证损失最低在第 {best_step} 步（{best_val:.3f}），开始在验证集上评估")
    cmd = [sys.executable, os.path.join(ROOT, "cdt503/scripts/eval_split.py"),
           "--split", "valid", "--adapter", best_dir, "--out", p.res]
    if smoke:
        cmd += ["--limit", str(SMOKE_EVAL_LIMIT)]
    with open(os.path.join(p.res, "eval_valid.log"), "w") as f:
        rc = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=ROOT).returncode
    if rc != 0:
        log(p, f"评估失败，见 {os.path.relpath(os.path.join(p.res, 'eval_valid.log'), ROOT)}")
        return False

    train_sec = sum(s.get("ended", s["started"]) - s["started"] for s in state["segments"])
    summary = {
        "name": p.name, "overrides": overrides,
        "rank": cfg["lora_parameters"]["rank"], "learning_rate": cfg["learning_rate"],
        "num_layers": cfg["num_layers"], "batch_size": cfg["batch_size"], "seed": cfg["seed"], "iters": cfg["iters"],
        **params, "best_step": best_step, "best_val_loss": best_val, "final_val_loss": val_curve[-1][1],
        "train_minutes": train_sec / 60, "resumed_at": [s["offset"] for s in state["segments"][1:]],
        "imported_from": state["segments"][0].get("imported_from"),
        "valid": json.load(open(os.path.join(p.res, "valid_metrics.json"))),
    }
    json.dump(summary, open(os.path.join(p.res, "summary.json"), "w"), ensure_ascii=False, indent=2)
    state["status"] = "done"
    save_state(p, state)
    v = summary["valid"]
    log(p, f"完成：JSON 合格 {v['JSON合格率']:.3f}，情感 {v['整体情感准确率']:.3f}，方面 F1 {v['方面F1']:.3f}，"
           f"{v['sec_per_item']:.2f} 秒/条，训练 {summary['train_minutes']:.0f} 分钟")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true", help="每组只训 10 步，验证集只评 16 条")
    ap.add_argument("--only", nargs="*", help="只跑这些组")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--stop-after", type=int, default=None, help="（测试续跑用）存到该步检查点后强行中断")
    args = ap.parse_args()

    names = args.only or list(RUNS)
    for name in names:
        overrides = RUNS[name]
        p = Paths(name, args.smoke)
        cfg = make_config(name, overrides, args.smoke)
        state = load_state(p)
        if args.dry_run:
            print(f"{name:16s} {state['status']:9s} rank={cfg['lora_parameters']['rank']:<3} "
                  f"lr={cfg['learning_rate']:<7} layers={cfg['num_layers']:<3} seed={cfg['seed']} iters={cfg['iters']}")
            continue
        if state["status"] == "done":
            log(p, "已完成，跳过")
            continue
        if name == "baseline" and not args.smoke:
            if not state["segments"]:
                import_baseline(p, state)
                save_state(p, state)
        elif not train(p, cfg, state, args.stop_after):
            log(p, "训练未完成，重新运行本脚本可续跑")
            if args.stop_after:
                return
            continue
        finish(p, cfg, state, overrides, args.smoke)


if __name__ == "__main__":
    main()
