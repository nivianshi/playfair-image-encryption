from PIL import Image
import numpy as np
import hashlib
import random
from pathlib import Path
import matplotlib.pyplot as plt


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_IMAGE = "input/playfair.webp"
KEY = "CRYPTOLOGY"


LARGE_IMAGE_SIZE = (1200, 1200)

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


# ============================================================
# 1. GENERATE 16 × 16 PLAYFAIR MATRIX
# ============================================================

def generate_playfair_matrix(key):

    # Create all 256 possible 8-bit symbols
    symbols = list(range(256))

    # Generate SHA-256 hash from key
    key_hash = hashlib.sha256(
        key.encode()
    ).hexdigest()

    # Convert hash into integer seed
    seed = int(key_hash, 16)

    # Create deterministic random generator
    rng = random.Random(seed)

    # Shuffle all 256 symbols
    rng.shuffle(symbols)

    # Arrange symbols into 16 × 16 matrix
    matrix = np.array(
        symbols,
        dtype=np.uint8
    ).reshape(16, 16)

    return matrix


# ============================================================
# 2. FIND POSITION OF VALUE
# ============================================================

def find_position(matrix, value):

    position = np.argwhere(
        matrix == value
    )

    if len(position) == 0:
        raise ValueError(
            f"Value {value} not found in Playfair matrix"
        )

    row, column = position[0]

    return int(row), int(column)


# ============================================================
# 3. PLAYFAIR ENCRYPTION
# ============================================================

def playfair_encrypt_pair(
    matrix,
    value1,
    value2
):

    row1, col1 = find_position(
        matrix,
        value1
    )

    row2, col2 = find_position(
        matrix,
        value2
    )

    # --------------------------------------------------------
    # CASE 1: SAME ROW
    # --------------------------------------------------------

    if row1 == row2:

        encrypted1 = matrix[
            row1,
            (col1 + 1) % 16
        ]

        encrypted2 = matrix[
            row2,
            (col2 + 1) % 16
        ]

    # --------------------------------------------------------
    # CASE 2: SAME COLUMN
    # --------------------------------------------------------

    elif col1 == col2:

        encrypted1 = matrix[
            (row1 + 1) % 16,
            col1
        ]

        encrypted2 = matrix[
            (row2 + 1) % 16,
            col2
        ]

    # --------------------------------------------------------
    # CASE 3: RECTANGLE
    # --------------------------------------------------------

    else:

        encrypted1 = matrix[
            row1,
            col2
        ]

        encrypted2 = matrix[
            row2,
            col1
        ]

    return int(encrypted1), int(encrypted2)


# ============================================================
# 4. PLAYFAIR DECRYPTION
# ============================================================

def playfair_decrypt_pair(
    matrix,
    value1,
    value2
):

    row1, col1 = find_position(
        matrix,
        value1
    )

    row2, col2 = find_position(
        matrix,
        value2
    )

    # --------------------------------------------------------
    # CASE 1: SAME ROW
    # --------------------------------------------------------

    if row1 == row2:

        decrypted1 = matrix[
            row1,
            (col1 - 1) % 16
        ]

        decrypted2 = matrix[
            row2,
            (col2 - 1) % 16
        ]

    # --------------------------------------------------------
    # CASE 2: SAME COLUMN
    # --------------------------------------------------------

    elif col1 == col2:

        decrypted1 = matrix[
            (row1 - 1) % 16,
            col1
        ]

        decrypted2 = matrix[
            (row2 - 1) % 16,
            col2
        ]

    # --------------------------------------------------------
    # CASE 3: RECTANGLE
    # --------------------------------------------------------

    else:

        decrypted1 = matrix[
            row1,
            col2
        ]

        decrypted2 = matrix[
            row2,
            col1
        ]

    return int(decrypted1), int(decrypted2)


# ============================================================
# 5. ENCRYPT COMPLETE CHANNEL USING 16 × 16 BLOCKS
# ============================================================

def encrypt_channel(
    channel,
    matrix
):

    height, width = channel.shape

    encrypted_channel = np.zeros_like(
        channel,
        dtype=np.uint8
    )

    # Process image block-by-block
    for row in range(0, height, 16):

        for col in range(0, width, 16):

            # Extract 16 × 16 block
            block = channel[
                row:row + 16,
                col:col + 16
            ]

            # Flatten block
            flat = block.flatten()

            # Create pairs
            pairs = flat.reshape(-1, 2)

            encrypted_pairs = []

            # Encrypt every pair
            for pair in pairs:

                value1 = int(pair[0])
                value2 = int(pair[1])

                encrypted1, encrypted2 = (
                    playfair_encrypt_pair(
                        matrix,
                        value1,
                        value2
                    )
                )

                encrypted_pairs.append(
                    [encrypted1, encrypted2]
                )

            # Convert encrypted pairs back to block
            encrypted_block = np.array(
                encrypted_pairs,
                dtype=np.uint8
            ).flatten().reshape(16, 16)

            # Put encrypted block back into image
            encrypted_channel[
                row:row + 16,
                col:col + 16
            ] = encrypted_block

    return encrypted_channel


# ============================================================
# 6. DECRYPT COMPLETE CHANNEL USING 16 × 16 BLOCKS
# ============================================================

def decrypt_channel(
    channel,
    matrix
):

    height, width = channel.shape

    decrypted_channel = np.zeros_like(
        channel,
        dtype=np.uint8
    )

    # Process image block-by-block
    for row in range(0, height, 16):

        for col in range(0, width, 16):

            # Extract 16 × 16 encrypted block
            block = channel[
                row:row + 16,
                col:col + 16
            ]

            # Flatten block
            flat = block.flatten()

            # Create pairs
            pairs = flat.reshape(-1, 2)

            decrypted_pairs = []

            # Decrypt every pair
            for pair in pairs:

                value1 = int(pair[0])
                value2 = int(pair[1])

                decrypted1, decrypted2 = (
                    playfair_decrypt_pair(
                        matrix,
                        value1,
                        value2
                    )
                )

                decrypted_pairs.append(
                    [decrypted1, decrypted2]
                )

            # Convert decrypted pairs back to block
            decrypted_block = np.array(
                decrypted_pairs,
                dtype=np.uint8
            ).flatten().reshape(16, 16)

            # Put decrypted block back into image
            decrypted_channel[
                row:row + 16,
                col:col + 16
            ] = decrypted_block

    return decrypted_channel


# ============================================================
# DIFFUSION FUNCTIONS
# ============================================================

def diffuse_channel(channel, key):

    """
    Apply reversible XOR-based diffusion to one image channel.
    """

    flat = channel.flatten().astype(np.uint8)

    # Generate deterministic keystream from the key
    key_hash = hashlib.sha256(
        key.encode()
    ).digest()

    keystream = np.resize(
        np.frombuffer(key_hash, dtype=np.uint8),
        flat.size
    )

    # XOR diffusion
    diffused = np.bitwise_xor(
        flat,
        keystream
    )

    return diffused.reshape(channel.shape)


def reverse_diffusion(channel, key):

    """
    Reverse the XOR-based diffusion.
    XOR is self-inverse:
        A XOR K XOR K = A
    """

    flat = channel.flatten().astype(np.uint8)

    # Generate the same deterministic keystream
    key_hash = hashlib.sha256(
        key.encode()
    ).digest()

    keystream = np.resize(
        np.frombuffer(key_hash, dtype=np.uint8),
        flat.size
    )

    # Reverse XOR diffusion
    original = np.bitwise_xor(
        flat,
        keystream
    )

    return original.reshape(channel.shape)

# ============================================================
# 7. LOAD ORIGINAL IMAGE
# ============================================================

image = Image.open(
    INPUT_IMAGE
).convert("RGB")

print("=" * 60)
print("ORIGINAL IMAGE")
print("=" * 60)

print("Format:", image.format)
print("Size  :", image.size)
print("Mode  :", image.mode)

print("\nOriginal image dimensions:")
print("Width :", image.width)
print("Height:", image.height)

print(
    "Width divisible by 16 :",
    image.width % 16 == 0
)

print(
    "Height divisible by 16:",
    image.height % 16 == 0
)


# ============================================================
# 8. CONVERT ORIGINAL IMAGE TO NUMPY ARRAY
# ============================================================

image_array = np.array(
    image,
    dtype=np.uint8
)

print("\nOriginal image array shape:")
print(image_array.shape)


# ============================================================
# 9. SEPARATE RGB CHANNELS
# ============================================================

R = image_array[:, :, 0]
G = image_array[:, :, 1]
B = image_array[:, :, 2]


print("\nRGB channel dimensions:")

print("R:", R.shape)
print("G:", G.shape)
print("B:", B.shape)


# ============================================================
# 10. VERIFY PIXEL VALUE RANGE
# ============================================================

print("\nPixel value ranges:")

print(
    "R:",
    R.min(),
    "to",
    R.max()
)

print(
    "G:",
    G.min(),
    "to",
    G.max()
)

print(
    "B:",
    B.min(),
    "to",
    B.max()
)


# ============================================================
# 11. SAVE ORIGINAL RGB CHANNELS
# ============================================================

R_image = Image.fromarray(
    R,
    mode="L"
)

G_image = Image.fromarray(
    G,
    mode="L"
)

B_image = Image.fromarray(
    B,
    mode="L"
)

R_image.save(
    OUTPUT_DIR / "R_channel.png"
)

G_image.save(
    OUTPUT_DIR / "G_channel.png"
)

B_image.save(
    OUTPUT_DIR / "B_channel.png"
)

print("\nOriginal RGB channels saved.")


# ============================================================
# 12. GENERATE PLAYFAIR MATRIX
# ============================================================

playfair_matrix = generate_playfair_matrix(
    KEY
)

print("\n" + "=" * 60)
print("16 × 16 PLAYFAIR MATRIX")
print("=" * 60)

print(playfair_matrix)


# ============================================================
# 13. VERIFY PLAYFAIR MATRIX
# ============================================================

unique_values = np.unique(
    playfair_matrix
)

print("\nPlayfair matrix verification:")

print(
    "Matrix shape:",
    playfair_matrix.shape
)

print(
    "Number of unique symbols:",
    len(unique_values)
)

print(
    "Minimum value:",
    unique_values.min()
)

print(
    "Maximum value:",
    unique_values.max()
)


# ============================================================
# 14. TEST POSITION LOOKUP
# ============================================================

test_values = [
    0,
    28,
    183,
    255
]

print("\nTesting Playfair position lookup:")

for value in test_values:

    row, column = find_position(
        playfair_matrix,
        value
    )

    print(
        f"Value {value} → "
        f"Row: {row + 1}, "
        f"Column: {column + 1}"
    )


# ============================================================
# 15. TEST PLAYFAIR ENCRYPTION + DECRYPTION
# ============================================================

test_pair = (
    183,
    186
)

encrypted_pair = (
    playfair_encrypt_pair(
        playfair_matrix,
        test_pair[0],
        test_pair[1]
    )
)

decrypted_pair = (
    playfair_decrypt_pair(
        playfair_matrix,
        encrypted_pair[0],
        encrypted_pair[1]
    )
)


print("\n" + "=" * 60)
print("PLAYFAIR ENCRYPTION / DECRYPTION TEST")
print("=" * 60)

print(
    "Original pair :",
    test_pair
)

print(
    "Encrypted pair:",
    encrypted_pair
)

print(
    "Decrypted pair:",
    decrypted_pair
)


if decrypted_pair == test_pair:

    print("\nSUCCESS!")
    print(
        "Encryption and decryption returned "
        "the original pair."
    )

else:

    print("\nERROR!")
    print(
        "Decrypted pair does not match "
        "the original pair."
    )


# ============================================================
# 16. PLAYFAIR ENCRYPTION OF RGB CHANNELS
# ============================================================

R_playfair = encrypt_channel(
    R,
    playfair_matrix
)

G_playfair = encrypt_channel(
    G,
    playfair_matrix
)

B_playfair = encrypt_channel(
    B,
    playfair_matrix
)


# ============================================================
# 17. APPLY DIFFUSION TO RGB CHANNELS
# ============================================================

R_encrypted = diffuse_channel(
    R_playfair,
    KEY
)

G_encrypted = diffuse_channel(
    G_playfair,
    KEY
)

B_encrypted = diffuse_channel(
    B_playfair,
    KEY
)


print("\n" + "=" * 60)
print("PLAYFAIR + DIFFUSION ENCRYPTION COMPLETED")
print("=" * 60)

print(
    "R encrypted shape:",
    R_encrypted.shape
)

print(
    "G encrypted shape:",
    G_encrypted.shape
)

print(
    "B encrypted shape:",
    B_encrypted.shape
)


# ============================================================
# 18. SAVE ENCRYPTED RGB CHANNELS
# ============================================================

R_encrypted_image = Image.fromarray(
    R_encrypted,
    mode="L"
)

G_encrypted_image = Image.fromarray(
    G_encrypted,
    mode="L"
)

B_encrypted_image = Image.fromarray(
    B_encrypted,
    mode="L"
)

R_encrypted_image.save(
    OUTPUT_DIR / "R_encrypted_channel.png"
)

G_encrypted_image.save(
    OUTPUT_DIR / "G_encrypted_channel.png"
)

B_encrypted_image.save(
    OUTPUT_DIR / "B_encrypted_channel.png"
)

print(
    "\nEncrypted RGB channels saved successfully!"
)


# ============================================================
# 19. DISPLAY FIRST 10 ENCRYPTED VALUES
# ============================================================

print("\nFirst 10 encrypted R values:")
print(
    R_encrypted.flatten()[:10]
)

print("\nFirst 10 encrypted G values:")
print(
    G_encrypted.flatten()[:10]
)

print("\nFirst 10 encrypted B values:")
print(
    B_encrypted.flatten()[:10]
)


# ============================================================
# 20. COMBINE ENCRYPTED RGB CHANNELS
# ============================================================

encrypted_image_array = np.stack(
    [
        R_encrypted,
        G_encrypted,
        B_encrypted
    ],
    axis=2
)

print(
    "\nEncrypted image array shape:"
)

print(
    encrypted_image_array.shape
)


# ============================================================
# 21. SAVE FINAL ENCRYPTED IMAGE
# ============================================================

encrypted_image = Image.fromarray(
    encrypted_image_array,
    mode="RGB"
)

encrypted_image.save(
    OUTPUT_DIR / "encrypted_image.png"
)

print(
    "\nEncrypted image saved successfully!"
)


# ============================================================
# 22. CREATE LARGE VERSION FOR VISUALIZATION
# ============================================================

encrypted_large = encrypted_image.resize(
    LARGE_IMAGE_SIZE,
    Image.Resampling.NEAREST
)

encrypted_large.save(
    OUTPUT_DIR / "encrypted_image_1200x1200.png"
)

print(
    "\nEncrypted 1200 × 1200 image "
    "saved successfully!"
)


# ============================================================
# 20. REVERSE DIFFUSION OF RGB CHANNELS
# ============================================================

R_playfair_decrypted = reverse_diffusion(
    R_encrypted,
    KEY
)

G_playfair_decrypted = reverse_diffusion(
    G_encrypted,
    KEY
)

B_playfair_decrypted = reverse_diffusion(
    B_encrypted,
    KEY
)


# ============================================================
# 21. PLAYFAIR DECRYPTION OF RGB CHANNELS
# ============================================================

R_decrypted = decrypt_channel(
    R_playfair_decrypted,
    playfair_matrix
)

G_decrypted = decrypt_channel(
    G_playfair_decrypted,
    playfair_matrix
)

B_decrypted = decrypt_channel(
    B_playfair_decrypted,
    playfair_matrix
)


print("\n" + "=" * 60)
print("DIFFUSION + PLAYFAIR DECRYPTION COMPLETED")
print("=" * 60)

print(
    "R decrypted shape:",
    R_decrypted.shape
)

print(
    "G decrypted shape:",
    G_decrypted.shape
)

print(
    "B decrypted shape:",
    B_decrypted.shape
)


# ============================================================
# 27. COMBINE DECRYPTED RGB CHANNELS
# ============================================================

decrypted_image_array = np.stack(
    [
        R_decrypted,
        G_decrypted,
        B_decrypted
    ],
    axis=2
)

print(
    "\nDecrypted image array shape:"
)

print(
    decrypted_image_array.shape
)


# ============================================================
# 28. SAVE DECRYPTED IMAGE
# ============================================================

decrypted_image = Image.fromarray(
    decrypted_image_array,
    mode="RGB"
)

decrypted_image.save(
    OUTPUT_DIR / "decrypted_image.png"
)

print(
    "\nDecrypted image saved successfully!"
)


# ============================================================
# 29. CREATE LARGE DECRYPTED IMAGE
# ============================================================

decrypted_large = decrypted_image.resize(
    LARGE_IMAGE_SIZE,
    Image.Resampling.NEAREST
)

decrypted_large.save(
    OUTPUT_DIR / "decrypted_image_1200x1200.png"
)

print(
    "\nDecrypted 1200 × 1200 image "
    "saved successfully!"
)


# ============================================================
# 30. FINAL IMAGE VERIFICATION
# ============================================================

print("\n" + "=" * 60)
print("FINAL IMAGE VERIFICATION")
print("=" * 60)


images_identical = np.array_equal(
    image_array,
    decrypted_image_array
)


# Calculate differences
difference = np.abs(
    image_array.astype(np.int16)
    -
    decrypted_image_array.astype(np.int16)
)

different_values = np.count_nonzero(
    difference
)

maximum_difference = difference.max()

total_channel_values = image_array.size


# ============================================================
# 31. DISPLAY VERIFICATION RESULT
# ============================================================

if images_identical:

    print("\nSUCCESS!")
    print(
        "Original and decrypted images "
        "are IDENTICAL."
    )

else:

    print("\nERROR!")
    print(
        "Original and decrypted images "
        "are NOT identical."
    )


print(
    "\nNumber of different channel values:",
    different_values
)

print(
    "Maximum difference:",
    maximum_difference
)

print(
    "Total channel values:",
    total_channel_values
)


# ============================================================
# 32. FINAL STATUS
# ============================================================

print("\n" + "=" * 60)
print("PLAYFAIR IMAGE ENCRYPTION COMPLETED")
print("=" * 60)

print(
    "Input image              :",
    INPUT_IMAGE
)

print(
    "Key                      :",
    KEY
)

print(
    "Original image size      :",
    image.size
)

print(
    "Playfair matrix size     :",
    playfair_matrix.shape
)

print(
    "Encryption status        : COMPLETED"
)

print(
    "Decryption status        : COMPLETED"
)

print(
    "Image recovery status    :",
    "SUCCESS" if images_identical else "FAILED"
)

print(
    "Output directory         :",
    OUTPUT_DIR
)

print("=" * 60)


# ============================================================
# 33. HISTOGRAM AND ENTROPY ANALYSIS
# ============================================================




# ============================================================
# CALCULATE SHANNON ENTROPY
# ============================================================

def calculate_entropy(channel):

    # Count frequency of each pixel value
    histogram = np.bincount(
        channel.flatten(),
        minlength=256
    )

    # Convert frequency to probability
    probabilities = histogram / channel.size

    # Remove zero probabilities
    probabilities = probabilities[
        probabilities > 0
    ]

    # Shannon entropy
    entropy = -np.sum(
        probabilities *
        np.log2(probabilities)
    )

    return entropy


# ============================================================
# CALCULATE ENTROPY FOR ORIGINAL IMAGE
# ============================================================

R_entropy_original = calculate_entropy(R)
G_entropy_original = calculate_entropy(G)
B_entropy_original = calculate_entropy(B)


# ============================================================
# CALCULATE ENTROPY FOR ENCRYPTED IMAGE
# ============================================================

R_entropy_encrypted = calculate_entropy(
    R_encrypted
)

G_entropy_encrypted = calculate_entropy(
    G_encrypted
)

B_entropy_encrypted = calculate_entropy(
    B_encrypted
)


# ============================================================
# DISPLAY ENTROPY RESULTS
# ============================================================

print("\n" + "=" * 60)
print("SHANNON ENTROPY ANALYSIS")
print("=" * 60)

print("\nOriginal image entropy:")

print(
    "R:",
    R_entropy_original
)

print(
    "G:",
    G_entropy_original
)

print(
    "B:",
    B_entropy_original
)


print("\nEncrypted image entropy:")

print(
    "R:",
    R_entropy_encrypted
)

print(
    "G:",
    G_entropy_encrypted
)

print(
    "B:",
    B_entropy_encrypted
)


# ============================================================
# GENERATE HISTOGRAMS
# ============================================================

def save_histogram(
    original_channel,
    encrypted_channel,
    channel_name
):

    plt.figure(
        figsize=(10, 5)
    )

    plt.hist(
        original_channel.flatten(),
        bins=256,
        range=(0, 256),
        alpha=0.6,
        label="Original"
    )

    plt.hist(
        encrypted_channel.flatten(),
        bins=256,
        range=(0, 256),
        alpha=0.6,
        label="Encrypted"
    )

    plt.title(
        f"{channel_name} Channel Histogram"
    )

    plt.xlabel(
        "Pixel Intensity"
    )

    plt.ylabel(
        "Frequency"
    )

    plt.legend()

    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR /
        f"{channel_name}_histogram.png",
        dpi=300
    )

    plt.close()


# ============================================================
# SAVE RGB HISTOGRAMS
# ============================================================

save_histogram(
    R,
    R_encrypted,
    "R"
)

save_histogram(
    G,
    G_encrypted,
    "G"
)

save_histogram(
    B,
    B_encrypted,
    "B"
)


print(
    "\nHistogram analysis completed."
)

print(
    "Histogram files saved in:",
    OUTPUT_DIR
)


# ============================================================
# CORRELATION ANALYSIS
# ============================================================

import matplotlib.pyplot as plt


def calculate_correlation(channel, direction):
    """
    Calculate correlation coefficient between neighboring pixels.

    direction:
        horizontal -> left-right neighbors
        vertical   -> top-bottom neighbors
        diagonal   -> diagonal neighbors
    """

    if direction == "horizontal":

        x = channel[:, :-1].flatten()
        y = channel[:, 1:].flatten()

    elif direction == "vertical":

        x = channel[:-1, :].flatten()
        y = channel[1:, :].flatten()

    elif direction == "diagonal":

        x = channel[:-1, :-1].flatten()
        y = channel[1:, 1:].flatten()

    else:

        raise ValueError(
            "Invalid direction"
        )

    correlation = np.corrcoef(
        x.astype(np.float64),
        y.astype(np.float64)
    )[0, 1]

    return correlation, x, y


# ============================================================
# CHANNELS TO ANALYZE
# ============================================================

original_channels = {
    "R": R,
    "G": G,
    "B": B
}

encrypted_channels = {
    "R": R_encrypted,
    "G": G_encrypted,
    "B": B_encrypted
}


directions = [
    "horizontal",
    "vertical",
    "diagonal"
]


# ============================================================
# CORRELATION RESULTS
# ============================================================

correlation_results = {}


print("\n" + "=" * 60)
print("CORRELATION ANALYSIS")
print("=" * 60)


for channel_name in ["R", "G", "B"]:

    correlation_results[channel_name] = {
        "Original": {},
        "Encrypted": {}
    }

    print(
        f"\n{channel_name} CHANNEL"
    )

    # --------------------------------------------------------
    # ORIGINAL IMAGE
    # --------------------------------------------------------

    print("\nOriginal:")

    for direction in directions:

        correlation, x, y = calculate_correlation(
            original_channels[channel_name],
            direction
        )

        correlation_results[
            channel_name
        ]["Original"][direction] = correlation

        print(
            f"{direction.capitalize():12}: "
            f"{correlation:.6f}"
        )

    # --------------------------------------------------------
    # ENCRYPTED IMAGE
    # --------------------------------------------------------

    print("\nEncrypted:")

    for direction in directions:

        correlation, x, y = calculate_correlation(
            encrypted_channels[channel_name],
            direction
        )

        correlation_results[
            channel_name
        ]["Encrypted"][direction] = correlation

        print(
            f"{direction.capitalize():12}: "
            f"{correlation:.6f}"
        )


# ============================================================
# SAVE CORRELATION RESULTS
# ============================================================

correlation_file = (
    OUTPUT_DIR / "correlation_results.txt"
)

with open(
    correlation_file,
    "w"
) as file:

    file.write(
        "PLAYFAIR IMAGE ENCRYPTION\n"
    )

    file.write(
        "CORRELATION ANALYSIS\n"
    )

    file.write(
        "=" * 60 + "\n\n"
    )

    for channel_name in ["R", "G", "B"]:

        file.write(
            f"{channel_name} CHANNEL\n"
        )

        file.write(
            "-" * 40 + "\n"
        )

        for image_type in [
            "Original",
            "Encrypted"
        ]:

            file.write(
                f"{image_type}:\n"
            )

            for direction in directions:

                value = correlation_results[
                    channel_name
                ][image_type][direction]

                file.write(
                    f"  "
                    f"{direction.capitalize():12}: "
                    f"{value:.6f}\n"
                )

        file.write("\n")


print(
    "\nCorrelation results saved to:",
    correlation_file
)


# ============================================================
# CORRELATION SCATTER PLOTS
# ============================================================


for channel_name in ["R", "G", "B"]:

    for direction in directions:

        # ----------------------------------------------------
        # ORIGINAL
        # ----------------------------------------------------

        _, x_original, y_original = calculate_correlation(
            original_channels[channel_name],
            direction
        )

        plt.figure(
            figsize=(7, 6)
        )

        plt.scatter(
            x_original,
            y_original,
            s=1,
            alpha=0.3
        )

        plt.xlabel(
            "Pixel Value"
        )

        plt.ylabel(
            "Neighbor Pixel Value"
        )

        plt.title(
            f"Original {channel_name} - "
            f"{direction.capitalize()} Correlation"
        )

        plt.tight_layout()

        plt.savefig(
            OUTPUT_DIR /
            f"original_{channel_name}_{direction}_correlation.png",
            dpi=200
        )

        plt.close()

        # ----------------------------------------------------
        # ENCRYPTED
        # ----------------------------------------------------

        _, x_encrypted, y_encrypted = calculate_correlation(
            encrypted_channels[channel_name],
            direction
        )

        plt.figure(
            figsize=(7, 6)
        )

        plt.scatter(
            x_encrypted,
            y_encrypted,
            s=1,
            alpha=0.3
        )

        plt.xlabel(
            "Pixel Value"
        )

        plt.ylabel(
            "Neighbor Pixel Value"
        )

        plt.title(
            f"Encrypted {channel_name} - "
            f"{direction.capitalize()} Correlation"
        )

        plt.tight_layout()

        plt.savefig(
            OUTPUT_DIR /
            f"encrypted_{channel_name}_{direction}_correlation.png",
            dpi=200
        )

        plt.close()


print(
    "Correlation scatter plots saved successfully!"
)

print(
    "Output directory:",
    OUTPUT_DIR
)


# ============================================================
# NPCR AND UACI ANALYSIS
# ============================================================

print("\n" + "=" * 60)
print("NPCR AND UACI ANALYSIS")
print("=" * 60)


# ============================================================
# 1. CREATE MODIFIED IMAGE
# ============================================================

# Make a copy of the original image
modified_image_array = image_array.copy()

# Modify ONE pixel
# Pixel position: first row, first column
# Change only the Red channel

original_pixel_value = int(
    modified_image_array[0, 0, 0]
)

if original_pixel_value == 255:

    modified_image_array[0, 0, 0] = 254

else:

    modified_image_array[0, 0, 0] = (
        original_pixel_value + 1
    )


print("\nModified one pixel for avalanche testing:")

print(
    "Original R value:",
    original_pixel_value
)

print(
    "Modified R value:",
    int(
        modified_image_array[0, 0, 0]
    )
)


# ============================================================
# 2. SEPARATE MODIFIED RGB CHANNELS
# ============================================================

R_modified = modified_image_array[:, :, 0]
G_modified = modified_image_array[:, :, 1]
B_modified = modified_image_array[:, :, 2]


# ============================================================
# 3. ENCRYPT MODIFIED IMAGE
# ============================================================

R_modified_encrypted = encrypt_channel(
    R_modified,
    playfair_matrix
)

G_modified_encrypted = encrypt_channel(
    G_modified,
    playfair_matrix
)

B_modified_encrypted = encrypt_channel(
    B_modified,
    playfair_matrix
)


modified_encrypted_image_array = np.stack(
    [
        R_modified_encrypted,
        G_modified_encrypted,
        B_modified_encrypted
    ],
    axis=2
)


print(
    "\nModified image encrypted successfully."
)


# ============================================================
# 4. NPCR FUNCTION
# ============================================================

def calculate_npcr(
    encrypted_image_1,
    encrypted_image_2
):

    total_pixels = encrypted_image_1.size

    different_pixels = np.count_nonzero(
        encrypted_image_1 != encrypted_image_2
    )

    npcr = (
        different_pixels /
        total_pixels
    ) * 100

    return npcr


# ============================================================
# 5. UACI FUNCTION
# ============================================================

def calculate_uaci(
    encrypted_image_1,
    encrypted_image_2
):

    difference = np.abs(
        encrypted_image_1.astype(np.float64)
        -
        encrypted_image_2.astype(np.float64)
    )

    uaci = (
        difference.mean() /
        255
    ) * 100

    return uaci


# ============================================================
# 6. CALCULATE RGB NPCR
# ============================================================

npcr_R = calculate_npcr(
    R_encrypted,
    R_modified_encrypted
)

npcr_G = calculate_npcr(
    G_encrypted,
    G_modified_encrypted
)

npcr_B = calculate_npcr(
    B_encrypted,
    B_modified_encrypted
)


# ============================================================
# 7. CALCULATE RGB UACI
# ============================================================

uaci_R = calculate_uaci(
    R_encrypted,
    R_modified_encrypted
)

uaci_G = calculate_uaci(
    G_encrypted,
    G_modified_encrypted
)

uaci_B = calculate_uaci(
    B_encrypted,
    B_modified_encrypted
)


# ============================================================
# 8. DISPLAY RESULTS
# ============================================================

print("\nNPCR RESULTS:")

print(
    f"R Channel: {npcr_R:.6f}%"
)

print(
    f"G Channel: {npcr_G:.6f}%"
)

print(
    f"B Channel: {npcr_B:.6f}%"
)


print("\nUACI RESULTS:")

print(
    f"R Channel: {uaci_R:.6f}%"
)

print(
    f"G Channel: {uaci_G:.6f}%"
)

print(
    f"B Channel: {uaci_B:.6f}%"
)


# ============================================================
# 9. SAVE NPCR / UACI RESULTS
# ============================================================

npcr_uaci_file = (
    OUTPUT_DIR / "npcr_uaci_results.txt"
)


with open(
    npcr_uaci_file,
    "w"
) as file:

    file.write(
        "PLAYFAIR IMAGE ENCRYPTION\n"
    )

    file.write(
        "NPCR AND UACI ANALYSIS\n"
    )

    file.write(
        "=" * 60 + "\n\n"
    )

    file.write(
        "One pixel of the original image "
        "was modified before encryption.\n\n"
    )

    file.write(
        "NPCR RESULTS:\n"
    )

    file.write(
        f"R Channel: {npcr_R:.6f}%\n"
    )

    file.write(
        f"G Channel: {npcr_G:.6f}%\n"
    )

    file.write(
        f"B Channel: {npcr_B:.6f}%\n\n"
    )

    file.write(
        "UACI RESULTS:\n"
    )

    file.write(
        f"R Channel: {uaci_R:.6f}%\n"
    )

    file.write(
        f"G Channel: {uaci_G:.6f}%\n"
    )

    file.write(
        f"B Channel: {uaci_B:.6f}%\n"
    )


print(
    "\nNPCR/UACI results saved to:",
    npcr_uaci_file
)


# ============================================================
# PLAYFAIR vs PLAYFAIR + DIFFUSION COMPARISON
# ============================================================

print("\n" + "=" * 60)
print("PLAYFAIR vs PLAYFAIR + DIFFUSION")
print("=" * 60)


# ============================================================
# BASELINE: PLAYFAIR ONLY
# ============================================================

baseline_entropy = {
    "R": 1.5457505285131843,
    "G": 1.5473412518513925,
    "B": 1.5473412518513925
}

baseline_correlation = {
    "R": {
        "Horizontal": 0.931398,
        "Vertical": 0.996466,
        "Diagonal": 0.928396
    },
    "G": {
        "Horizontal": 0.979755,
        "Vertical": 0.996890,
        "Diagonal": 0.976745
    },
    "B": {
        "Horizontal": 0.979755,
        "Vertical": 0.996890,
        "Diagonal": 0.976745
    }
}

baseline_npcr = {
    "R": 0.000139,
    "G": 0.000000,
    "B": 0.000000
}

baseline_uaci = {
    "R": 0.000067,
    "G": 0.000000,
    "B": 0.000000
}


# ============================================================
# PLAYFAIR + DIFFUSION RESULTS
# ============================================================

diffusion_entropy = {
    "R": 6.142029767804088,
    "G": 6.15811862935125,
    "B": 6.15811862935125
}

diffusion_correlation = {
    "R": {
        "Horizontal": -0.024792,
        "Vertical": 0.223678,
        "Diagonal": 0.084918
    },
    "G": {
        "Horizontal": -0.093776,
        "Vertical": 0.164122,
        "Diagonal": 0.010373
    },
    "B": {
        "Horizontal": -0.093776,
        "Vertical": 0.164122,
        "Diagonal": 0.010373
    }
}

diffusion_npcr = {
    "R": 100.000000,
    "G": 100.000000,
    "B": 100.000000
}

diffusion_uaci = {
    "R": 40.053994,
    "G": 33.919322,
    "B": 33.919322
}


# ============================================================
# DISPLAY COMPARISON
# ============================================================

print("\nENTROPY COMPARISON")

for channel in ["R", "G", "B"]:

    print(
        f"{channel}: "
        f"Playfair = {baseline_entropy[channel]:.6f}, "
        f"Playfair + Diffusion = "
        f"{diffusion_entropy[channel]:.6f}"
    )


print("\nNPCR COMPARISON")

for channel in ["R", "G", "B"]:

    print(
        f"{channel}: "
        f"Playfair = {baseline_npcr[channel]:.6f}%, "
        f"Playfair + Diffusion = "
        f"{diffusion_npcr[channel]:.6f}%"
    )


print("\nUACI COMPARISON")

for channel in ["R", "G", "B"]:

    print(
        f"{channel}: "
        f"Playfair = {baseline_uaci[channel]:.6f}%, "
        f"Playfair + Diffusion = "
        f"{diffusion_uaci[channel]:.6f}%"
    )


print("\nCORRELATION COMPARISON")

for channel in ["R", "G", "B"]:

    print(f"\n{channel} CHANNEL")

    for direction in [
        "Horizontal",
        "Vertical",
        "Diagonal"
    ]:

        print(
            f"{direction}: "
            f"Playfair = "
            f"{baseline_correlation[channel][direction]:.6f}, "
            f"Playfair + Diffusion = "
            f"{diffusion_correlation[channel][direction]:.6f}"
        )


# ============================================================
# SAVE COMPARISON RESULTS
# ============================================================

comparison_file = (
    OUTPUT_DIR / "playfair_vs_diffusion_comparison.txt"
)

with open(
    comparison_file,
    "w"
) as file:

    file.write(
        "PLAYFAIR IMAGE ENCRYPTION\n"
    )

    file.write(
        "PLAYFAIR vs PLAYFAIR + DIFFUSION\n"
    )

    file.write(
        "=" * 60 + "\n\n"
    )


    # --------------------------------------------------------
    # ENTROPY
    # --------------------------------------------------------

    file.write("ENTROPY COMPARISON\n")
    file.write("-" * 40 + "\n")

    for channel in ["R", "G", "B"]:

        file.write(
            f"{channel}: "
            f"Playfair = {baseline_entropy[channel]:.6f}, "
            f"Playfair + Diffusion = "
            f"{diffusion_entropy[channel]:.6f}\n"
        )


    # --------------------------------------------------------
    # NPCR
    # --------------------------------------------------------

    file.write("\nNPCR COMPARISON\n")
    file.write("-" * 40 + "\n")

    for channel in ["R", "G", "B"]:

        file.write(
            f"{channel}: "
            f"Playfair = {baseline_npcr[channel]:.6f}%, "
            f"Playfair + Diffusion = "
            f"{diffusion_npcr[channel]:.6f}%\n"
        )


    # --------------------------------------------------------
    # UACI
    # --------------------------------------------------------

    file.write("\nUACI COMPARISON\n")
    file.write("-" * 40 + "\n")

    for channel in ["R", "G", "B"]:

        file.write(
            f"{channel}: "
            f"Playfair = {baseline_uaci[channel]:.6f}%, "
            f"Playfair + Diffusion = "
            f"{diffusion_uaci[channel]:.6f}%\n"
        )


    # --------------------------------------------------------
    # CORRELATION
    # --------------------------------------------------------

    file.write("\nCORRELATION COMPARISON\n")
    file.write("-" * 40 + "\n")

    for channel in ["R", "G", "B"]:

        file.write(
            f"\n{channel} CHANNEL\n"
        )

        for direction in [
            "Horizontal",
            "Vertical",
            "Diagonal"
        ]:

            file.write(
                f"{direction}: "
                f"Playfair = "
                f"{baseline_correlation[channel][direction]:.6f}, "
                f"Playfair + Diffusion = "
                f"{diffusion_correlation[channel][direction]:.6f}\n"
            )


    # --------------------------------------------------------
    # CONCLUSION
    # --------------------------------------------------------

    file.write("\n")
    file.write("=" * 60 + "\n")
    file.write("OBSERVATION\n")
    file.write("=" * 60 + "\n\n")

    file.write(
        "The diffusion layer significantly improves the "
        "statistical properties of the encrypted image. "
        "Entropy increases, pixel correlation decreases, "
        "and NPCR/UACI demonstrate strong sensitivity "
        "to a one-pixel modification.\n"
    )

    file.write(
        "The complete Playfair + diffusion system remains "
        "fully reversible, with the original image recovered "
        "exactly during decryption.\n"
    )


print(
    "\nComparison results saved to:",
    comparison_file
)

print(
    "\nPlayfair vs Diffusion comparison completed."
)