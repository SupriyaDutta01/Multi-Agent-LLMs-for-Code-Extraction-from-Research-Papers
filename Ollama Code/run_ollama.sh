#!/bin/bash

PAPER_NAME="Transformer"
PAPER_FORMAT="JSON"
PDF_JSON_PATH="/home/supriyo/Desktop/Project/Paper2Code-master/examples/Transformer_cleaned.json"
OUTPUT_DIR="/home/supriyo/Desktop/Project/Paper2Code-master/outputs_llama3/Transformer_dscoder"
OUTPUT_REPO_DIR="/home/supriyo/Desktop/Project/Paper2Code-master/outputs_llama3/Transformer_dscoder_repo"

mkdir -p $OUTPUT_DIR
mkdir -p $OUTPUT_REPO_DIR

python3 1_planning_ollama.py \
  --paper_name "$PAPER_NAME" \
  --paper_format "$PAPER_FORMAT" \
  --pdf_json_path "$PDF_JSON_PATH" \
  --output_dir "$OUTPUT_DIR" \
  --model_name "llama3"

python3 1.1_extract_ollama_config.py \
    --paper_name $PAPER_NAME \
    --output_dir ${OUTPUT_DIR}

cp -rp ${OUTPUT_DIR}/planning_config.yaml ${OUTPUT_REPO_DIR}/config.yaml


python3 2_analyzing_ollama.py \
  --paper_name "$PAPER_NAME" \
  --paper_format "$PAPER_FORMAT" \
  --pdf_json_path "$PDF_JSON_PATH" \
  --output_dir "$OUTPUT_DIR" \
  --model_name "llama3"




python3 3_coding_ollama.py \
  --paper_name "$PAPER_NAME" \
  --paper_format "$PAPER_FORMAT" \
  --pdf_json_path "$PDF_JSON_PATH" \
  --output_dir "$OUTPUT_DIR" \
  --output_repo_dir ${OUTPUT_REPO_DIR} \
  --model_name "llama3"
 

