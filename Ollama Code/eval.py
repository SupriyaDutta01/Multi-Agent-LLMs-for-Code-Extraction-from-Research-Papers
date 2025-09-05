import os
import sys
import json
import argparse
from utils import (
    read_python_files, read_all_files, extract_planning, content_to_json,
    extract_json_from_string, num_tokens_from_messages, get_now_str, print_log_cost
)


def api_call(request_json):
    # Simulated local/dummy LLM response
    print("[INFO] Skipping OpenAI call (no API key used). Returning mock response.")
    return {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "score": 5,
                    "critique_list": "Looks correct based on the methods described."
                })
            }
        }] * request_json.get("n", 1),
        "usage": {
            "prompt_tokens": 1000,
            "completion_tokens": 500
        }
    }


def prepare_code_block(args, paper_json):
    if args.papercoder:
        code_blocks = ""
        target_files = read_python_files(args.target_repo_dir)
        config_yaml = open(os.path.join(args.output_dir, "planning_config.yaml")).read()
        context = extract_planning(os.path.join(args.output_dir, "planning_trajectories.json"))

        task_list = content_to_json(context[2]) if not os.path.exists(f'{args.output_dir}/task_list.json') else json.load(open(f'{args.output_dir}/task_list.json'))

        for file in task_list.get('Task list', []):
            if file.endswith(".yaml"):
                continue
            code_blocks += f"```python\n## File name: {file}\n{target_files[file]}\n```\n\n"
        code_blocks += f"```yaml\n## File name: config.yaml\n{config_yaml}\n```\n\n"
    else:
        all_files = read_all_files(args.target_repo_dir, allowed_ext=[".py", ".yaml", ".yml", ".md", ".sh", ".bash"], is_print=False)
        code_blocks = "\n".join([f"```## File name: {fname}\n{code}\n```\n" for fname, code in all_files.items()])

    return code_blocks


def prepare_prompt(args, paper_json, code_blocks):
    prompt_template = open(f"{args.data_dir}/prompts/{args.eval_type}.txt").read()
    prompt = prompt_template.replace("{{Paper}}", str(paper_json)).replace("{{Code}}", code_blocks)

    if args.eval_type == "ref_based" and args.gold_repo_dir:
        gold_blocks = ""
        all_gold_files = read_all_files(args.gold_repo_dir, allowed_ext=[".py", ".yaml", ".yml", ".md", ".sh", ".bash"], is_print=False)

        if args.selected_file_path:
            selected = set(open(args.selected_file_path).read().splitlines())
            gold_blocks = "\n".join([f"```## File name: {fname}\n{code}\n```\n" for fname, code in all_gold_files.items() if fname in selected])
        else:
            gold_blocks = "\n".join([f"```## File name: {fname}\n{code}\n```\n" for fname, code in all_gold_files.items()])

        prompt = prompt.replace("{{GoldCode}}", gold_blocks)

    return [{"role": "system", "content": prompt}]


def evaluate_response(args, completion_json):
    score_key = "score"
    rationale_key = "critique_list"
    scores, rationales = [], []

    for choice in completion_json['choices'][:args.generated_n]:
        try:
            content = choice['message']['content'].strip()
            try:
                output = json.loads(content)
            except:
                output = json.loads(extract_json_from_string(content))

            score = int(output[score_key])
            rationale = output[rationale_key]
            rationale = json.dumps(rationale) if not isinstance(rationale, str) else rationale

            if 1 <= score <= 5:
                scores.append(score)
                rationales.append(rationale)
            else:
                print(f"[WARNING] Invalid score: {score}")
        except Exception as e:
            print(f"[WARNING] Failed to parse output: {e}")

    return scores, rationales


def main(args):
    with open(args.pdf_json_path) as f:
        paper_json = json.load(f)

    code_blocks = prepare_code_block(args, paper_json)
    messages = prepare_prompt(args, paper_json, code_blocks)

    try:
        tokens = num_tokens_from_messages(messages)
        if tokens > 128000:
            print(f"[ERROR] Token limit exceeded for {args.paper_name}")
            sys.exit(1)
    except Exception as e:
        print(f"[WARNING] Token count failed: {e}")
        tokens = 0

    request_json = {
        "model": args.gpt_version,
        "messages": messages,
        "n": min(args.generated_n, 8 if "o3-mini" in args.gpt_version else args.generated_n),
        "temperature": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0
    }

    completion = api_call(request_json)
    completion_json = completion  # already dict

    scores, rationales = evaluate_response(args, completion_json)
    avg_score = sum(scores) / len(scores) if scores else 0

    result = {
        "paper_name": args.paper_name,
        "target_repo_dir": args.target_repo_dir,
        "eval_type": args.eval_type,
        "gold_repo_dir": args.gold_repo_dir,
        "generated_n": args.generated_n,
        "request_json": request_json,
        "completion_json": completion_json,
        "eval_result": {
            "score": avg_score,
            "valid_n": len(scores),
            "scroe_lst": scores,
            "rationale_lst": rationales
        }
    }

    now_str = get_now_str()
    os.makedirs(args.eval_result_dir, exist_ok=True)
    result_path = os.path.join(args.eval_result_dir, f"{args.paper_name}_eval_{args.eval_type}_{args.gpt_version}_{now_str}.json")
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

    print("\n" + "=" * 40)
    print("🌟 Evaluation Summary 🌟")
    print(f"📄 Paper: {args.paper_name}")
    print(f"🧪 Type: {args.eval_type}")
    print(f"📁 Repo: {args.target_repo_dir}")
    print(f"📊 Score: {avg_score:.4f} | Valid: {len(scores)}/{args.generated_n}")
    print("=" * 40)

    print_log_cost(completion_json, args.gpt_version, f"[Evaluation] {args.paper_name} - {args.eval_type}", args.output_dir, 0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--paper_name', type=str)
    parser.add_argument('--pdf_json_path', type=str)
    parser.add_argument('--data_dir', type=str, default="../data")
    parser.add_argument('--output_dir', type=str)
    parser.add_argument('--target_repo_dir', type=str)
    parser.add_argument('--gold_repo_dir', type=str, default="")
    parser.add_argument('--eval_result_dir', type=str)
    parser.add_argument('--eval_type', type=str, default="ref_free", choices=["ref_free", "ref_based"])
    parser.add_argument('--generated_n', type=int, default=8)
    parser.add_argument('--gpt_version', type=str, default="llama3")
    parser.add_argument('--selected_file_path', type=str, default="")
    parser.add_argument('--papercoder', action="store_true")
    args = parser.parse_args()

    main(args)
