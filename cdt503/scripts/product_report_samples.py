"""在三个内置样例上离线生成商品报告，存成文件，供报告正文和演示脚本引用。

和 Gradio 商品报告页走同一套逻辑（product_report.py）、同一个模型和同样的批大小（8），
所以结果应该和网页上点 Generate report 一致。不需要开网页，也不和网页同时跑（GPU 内存）。

用法：uv run python cdt503/scripts/product_report_samples.py [--samples hotel tablet fruit]
输出：cdt503/results/product_report/<样例>/summary.json、report.csv、aspects.png、raw.jsonl
"""
import argparse
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, os.path.join(ROOT, "cdt503"))
import product_report  # noqa: E402

STUDENT = "mlx-community/Qwen3-1.7B-bf16"
MAX_CHARS = 300  # 和 app_gradio.py 一致：超长评论截断
ADAPTER = os.path.join(ROOT, "cdt503/runs/sweep/lr5e-5/best")
OUT = os.path.join(ROOT, "cdt503/results/product_report")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", nargs="+", default=["hotel", "tablet", "fruit"])
    ap.add_argument("--adapter", default=ADAPTER)
    args = ap.parse_args()

    from gen import extract, load_model
    model, tok = load_model(STUDENT, adapter_path=args.adapter)
    print(f"已加载 {STUDENT} + {os.path.relpath(args.adapter, ROOT)}", flush=True)

    for name in args.samples:
        path = os.path.join(ROOT, f"cdt503/demo/samples/{name}.csv")
        rows = product_report.read_reviews("", path)
        texts = [t[:MAX_CHARS] for t, _ in rows]
        labels = [lab for _, lab in rows]
        t0 = time.time()
        raws = extract(model, tok, texts, batch_size=8, log_every=5)
        secs = time.time() - t0
        rep = product_report.build_report(texts, raws, labels)

        out = os.path.join(OUT, name)
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, "raw.jsonl"), "w", encoding="utf-8") as f:
            for t, r in zip(texts, raws):
                f.write(json.dumps({"text": t, "raw": r}, ensure_ascii=False) + "\n")
        product_report.to_csv(os.path.join(out, "report.csv"), texts, rep, labels)
        product_report.plot(rep).savefig(os.path.join(out, "aspects.png"), dpi=200)
        summary = {k: v for k, v in rep.items() if k != "parsed"}
        summary.update({"sample": name, "adapter": os.path.relpath(args.adapter, ROOT),
                        "seconds": round(secs, 1), "sec_per_review": round(secs / len(texts), 3)})
        with open(os.path.join(out, "summary.json"), "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        print(f"\n{name}：{rep['n']} 条，{secs:.0f} 秒；好评 {rep['pos_rate']:.0%}"
              f"（星级 {rep['label_pos_rate']:.0%}），整体判断与星级一致 {rep['label_agreement']:.0%}，"
              f"不合格输出 {rep['n_invalid']}")
        print("  最受好评：" + "、".join(f"{a['aspect_en']} {a['pos']}" for a in rep["top_praised"]))
        print("  最常被抱怨：" + "、".join(f"{a['aspect_en']} {a['neg']}" for a in rep["top_complaints"]))
        for a in rep["aspects"][:6]:
            print(f"  {a['aspect_en']:<22} 提及 {a['mentions']:>3}  +{a['pos']} / -{a['neg']}")


if __name__ == "__main__":
    main()
