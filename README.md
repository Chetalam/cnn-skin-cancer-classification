# CNN Skin Cancer Classification System

Student: Limo, Laura Chetalam | 169388 | BBIT 4D
Supervisor: Dr. Henry Muchiri
Institution: Strathmore University, School of Computing and Engineering Sciences
Year: 2026

## Project Overview

A deep learning system that classifies skin cancer lesions into three categories:
Melanoma (MEL), Squamous Cell Carcinoma (SCC), and Basal Cell Carcinoma (BCC).
Built using CNN transfer learning and deployed as a Streamlit web application
for non-specialist healthcare workers in low-resource settings.

## CNN Architectures Evaluated

- MobileNetV2 — Primary candidate, lightweight
- EfficientNet-B0 — Primary candidate, efficient
- ResNet50 — Benchmark comparison

## Datasets

- HAM10000: 10,015 dermoscopy images — Kaggle / ISIC
- PAD-UFES-20: 2,298 clinical images — Kaggle / Mendeley

Both datasets are stored in Google Drive. See data/README.md for links.

## Target Performance

- Accuracy: at least 85%
- F1-score (macro): at least 0.80
- Sensitivity per class: at least 0.80