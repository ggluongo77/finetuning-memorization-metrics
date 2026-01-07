# LLM Finetuning Memorization Metrics

This repository contains the implementation and experimental framework for analyzing unintended memorization in autoregressive Language Models during the fine-tuning phase. 
The project compares traditional privacy metrics with recently proposed nuanced measures to evaluate how models "remember" sensitive information (canaries) across different architectures and scaling factors.

The core of this research is to demonstrate that traditional "recollection-based" or "verbatim extraction" metrics often fail to capture the true extent of privacy risks in small-to-medium LLMs. By implementing **Contextual** and **Counterfactual** memorization metrics, we provide a more granular view of information leakage.

