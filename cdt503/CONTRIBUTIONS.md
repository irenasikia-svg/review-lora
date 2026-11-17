# Team Contributions — CDT503 Final Project

| | Member A | Member B |
|---|---|---|
| Name | Han Daiyuan | Li Mingtai |
| Student ID | 3231363 | 3231959 |

"A" and "B" are the same identifiers used for the human annotation (`cdt503/data/aspect_gold_A.jsonl`, `aspect_gold_B.jsonl`).

## Division of work

Each member owns one end-to-end part independently; shared tasks are listed separately.

| Area | Owner | What this person did / is responsible for |
|---|---|---|
| Data pipeline & distillation | Han Daiyuan | Data cleaning and stratified sampling; teacher labelling with Qwen3-30B-A3B; quality filter; label schema revision (v1 → v2) and its inter-annotator check |
| Training & hyper-parameter study | Li Mingtai | LoRA training setup; the 10-run sweep (rank, learning rate, layers, seed, scale); checkpoint selection; final test-set evaluation |
| Human evaluation | Han Daiyuan | Sampling 100 never-used reviews; the labelling and adjudication tools; evaluation and error analysis |
| Gradio prototype | Li Mingtai | Single-model LoRA on/off design; inference thread and queue; stress test; DEMO.md fall-back plan |
| Report | Han Daiyuan: §I–II · Li Mingtai: §III–IV | Each writes and checks their sections; both proof-read the whole report |

## Shared tasks

| Task | Both members |
|---|---|
| Human annotation | 60 reviews each (20 shared for agreement) |
| Adjudication | Jointly reviewed the 20 disagreeing / contradictory labels |

## Tools

Development used Python (MLX, MLX-LM, Gradio) on an Apple M5 laptop, and an AI coding assistant (Claude Code) for
writing and debugging code and drafting documents; all design decisions, annotations, and final checks were made by the
team.

> 提示：上面的分工是根据项目结构起草的模板，请你们按实际情况调整"负责人"一栏，确保每人都有一块能独立讲清楚的部分。
> "Tools" 一段是否保留由你们决定（课程允许使用 AI；如实说明通常是加分项）。
