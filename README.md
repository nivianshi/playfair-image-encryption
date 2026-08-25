@"

\# Playfair Image Encryption with Diffusion



\## Overview



This project implements an image encryption scheme based on a 256-symbol Playfair cipher combined with a reversible XOR-based diffusion layer.



The project evaluates the effect of the diffusion layer on the statistical properties of encrypted images using Shannon entropy, histogram analysis, pixel correlation, NPCR, and UACI.



\## Encryption Pipeline



Input Image

&#x20;   ↓

RGB Channel Separation

&#x20;   ↓

16 × 16 Block Processing

&#x20;   ↓

Playfair Encryption

&#x20;   ↓

XOR Diffusion

&#x20;   ↓

Encrypted Image



\## Decryption Pipeline



Encrypted Image

&#x20;   ↓

Reverse XOR Diffusion

&#x20;   ↓

Playfair Decryption

&#x20;   ↓

RGB Reconstruction

&#x20;   ↓

Recovered Image



\## Features



\- 16 × 16 Playfair matrix

\- 256 possible 8-bit pixel symbols

\- SHA-256 based key-dependent matrix generation

\- Playfair pair encryption and decryption

\- 16 × 16 image block processing

\- Reversible XOR-based diffusion

\- RGB image encryption

\- Exact image recovery verification

\- Shannon entropy analysis

\- Histogram analysis

\- Horizontal, vertical, and diagonal pixel correlation analysis

\- NPCR analysis

\- UACI analysis

\- Playfair-only vs Playfair + Diffusion comparison



\## Experimental Results



The implementation was tested using a 1200 × 1200 RGB image.



\### Image Recovery



The original image was recovered exactly after encryption and decryption.



\- Different channel values: `0`

\- Maximum difference: `0`

\- Total channel values: `4,320,000`

\- Recovery status: `SUCCESS`



\### Shannon Entropy



| Channel | Original | Playfair + Diffusion |

|---|---:|---:|

| R | 1.514579 | 6.142030 |

| G | 1.514579 | 6.158119 |

| B | 1.514579 | 6.158119 |



\### Correlation



Encrypted-image correlation was substantially reduced compared with the original image.



| Channel | Direction | Original | Encrypted |

|---|---|---:|---:|

| R | Horizontal | 0.989442 | -0.024792 |

| R | Vertical | 0.989806 | 0.223678 |

| R | Diagonal | 0.979356 | 0.084918 |

| G | Horizontal | 0.993207 | -0.093776 |

| G | Vertical | 0.993813 | 0.164122 |

| G | Diagonal | 0.987078 | 0.010373 |

| B | Horizontal | 0.993207 | -0.093776 |

| B | Vertical | 0.993813 | 0.164122 |

| B | Diagonal | 0.987078 | 0.010373 |



\### NPCR and UACI



A single pixel in the original image was modified before re-encryption.



| Channel | NPCR | UACI |

|---|---:|---:|

| R | 100.000000% | 40.053994% |

| G | 100.000000% | 33.919322% |

| B | 100.000000% | 33.919322% |



\### Effect of Diffusion



The experimental comparison showed that adding the diffusion layer significantly improved the statistical characteristics of the encrypted image.



| Metric | Playfair Only | Playfair + Diffusion |

|---|---:|---:|

| R Entropy | 1.545751 | 6.142030 |

| G Entropy | 1.547341 | 6.158119 |

| B Entropy | 1.547341 | 6.158119 |

| R NPCR | 0.000139% | 100% |

| G NPCR | 0% | 100% |

| B NPCR | 0% | 100% |



The comparison demonstrates the importance of the diffusion stage for improving resistance to statistical and differential analysis.



\## Technologies



\- Python

\- NumPy

\- Pillow

\- Matplotlib

\- SHA-256



\## Project Structure



```text

playfair-image-encryption/

│

├── main.py

├── README.md

├── requirements.txt

├── .gitignore

│

├── input/

│   └── playfair.webp

│

└── output/

&#x20;   └── Generated encryption and analysis results

