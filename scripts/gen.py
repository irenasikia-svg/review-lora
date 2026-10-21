"""批量让模型做抽取。老师标注和评估学生都用这里。"""
import time

from mlx_lm import batch_generate, load

from common import build_messages


def load_model(path, adapter_path=None):
    return load(path, adapter_path=adapter_path)


def encode(tokenizer, text, with_examples=False):
    # enable_thinking=False：Qwen3 默认会先"思考"再回答，这个任务不需要，关掉更快
    return tokenizer.apply_chat_template(
        build_messages(text, with_examples), add_generation_prompt=True, enable_thinking=False
    )


def extract(model, tokenizer, texts, batch_size=16, max_tokens=256, log_every=1, sampler=None,
            with_examples=False):
    """sampler 为 None 时每次都选概率最高的字（结果固定）；传入带温度的 sampler 会引入随机性。
    with_examples=True 时在提示词里附上标注示例（给老师用）。"""
    outputs = []
    start = time.time()
    for i in range(0, len(texts), batch_size):
        chunk = texts[i:i + batch_size]
        prompts = [encode(tokenizer, t, with_examples) for t in chunk]
        resp = batch_generate(model, tokenizer, prompts, max_tokens=max_tokens, sampler=sampler)
        outputs.extend(resp.texts)
        if (i // batch_size) % log_every == 0:
            done = len(outputs)
            speed = done / (time.time() - start)
            print(f"  {done}/{len(texts)}  {speed:.1f} 条/秒", flush=True)
    return outputs
