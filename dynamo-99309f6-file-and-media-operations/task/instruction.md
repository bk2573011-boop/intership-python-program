You are tasked with processing an archive located at `/app/data/archive.zip`.

Perform the following steps:
1. Extract `/app/data/archive.zip` into a temporary directory.
2. Group the files by their file extensions (.txt, .jpg, .csv).
3. Create separate `.tar.gz` archives for each group under `/app/output/`:
   - `/app/output/text_files.tar.gz` containing all `.txt` files.
   - `/app/output/image_files.tar.gz` containing all `.jpg` files.
   - `/app/output/data_files.tar.gz` containing all `.csv` files.

Ensure all outputs are placed exactly in `/app/output/`.
