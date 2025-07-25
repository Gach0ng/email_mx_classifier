# email_mx_classifier
批量对邮箱mx记录进行分类
# Email MX Record Classifier

A Python tool that classifies email addresses based on their MX records, with support for custom classification rules and incremental processing.

## Features

- Classifies emails by querying their MX records
- Supports predefined classification rules for major email services
- Allows custom MX record classification via a dictionary file
- Incremental processing to avoid redundant MX record queries
- Secondary classification for refining results
- Detailed output with progress tracking

## Classification Logic

The tool uses a two-step classification process:

1. **Primary Classification** (built-in rules):
   - `Microsoft`: Emails with MX records ending in `mail.protection.outlook.com`
   - `Outlook`: Emails with MX records ending in `outlook.com` (but not matching the above)
   - `Gmail_Personal`: Emails with Gmail MX records (`google.com`) and `@gmail.com` domain
   - `Gmail_Enterprise`: Emails with Gmail MX records but non-gmail.com domains
   - `Other`: All other emails, stored with their MX records

2. **Secondary Classification**:
   - Uses a custom MX dictionary file to reclassify emails from the `Other` category

## Requirements

- Python 3.6+
- Required packages:
  ```bash
  pip install dnspython tqdm
  ```

## Installation

1. Clone or download this repository
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Command Structure

```bash
python email_mx_classifier.py --input <input_file> [--output <output_dir>] [--mx-dict <dict_file>] [--reuse-existing]
```

### Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--input` | Yes | Path to input text file containing email addresses (one per line) |
| `--output` | No | Path to output directory (default: `classified_emails`) |
| `--mx-dict` | No | Path to MX dictionary file for custom classification rules |
| `--reuse-existing` | No | Enable incremental processing (reuse existing classification results) |

### MX Dictionary File Format

The MX dictionary file uses a simple format where each line contains an MX record suffix and its corresponding category, separated by a colon:

```
office365.us:Microsoft
aspmx.l.google.com:Gmail_Enterprise
mail.protection.outlook.de:Microsoft
yahoo.com:Yahoo
```

## Workflow

1. **Prepare your input file** with one email address per line
2. **(Optional)** Create an MX dictionary file for custom classifications
3. **Run the initial classification** to process all emails
4. **Update your MX dictionary** as needed for better classification
5. **Run with --reuse-existing** to incrementally process new emails and reclassify existing ones using the updated dictionary

## Examples

### Initial Classification

```bash
python email_mx_classifier.py --input emails.txt --output classified --mx-dict mx_rules.txt
```

### Incremental Processing (After Updating MX Dictionary)

```bash
python email_mx_classifier.py --input emails.txt --output classified --mx-dict mx_rules.txt --reuse-existing
```

### Simple Classification Without Custom Rules

```bash
python email_mx_classifier.py --input emails.txt --output results
```

## Output

The tool creates the following files in the output directory:

- `Microsoft.txt`: Emails classified as Microsoft services
- `Outlook.txt`: Emails classified as Outlook
- `Gmail_Personal.txt`: Personal Gmail accounts
- `Gmail_Enterprise.txt`: Google Workspace (G Suite) accounts
- `Other.txt`: Emails not matching any classification rules (format: `email:mx_record`)
- `invalid_format.txt`: Emails with invalid format

## Notes

- MX record queries may take time depending on the number of emails and network conditions
- The `--reuse-existing` option significantly speeds up subsequent runs by skipping already classified emails
- The secondary classification step (using MX dictionary) always runs when a dictionary file is provided, ensuring classifications stay up-to-date with your rules
- Network issues may cause some MX record queries to fail - these emails will be placed in the `Other` category

## Troubleshooting

- **DNS Resolution Errors**: Ensure you have a working internet connection and DNS server access
- **Large Input Files**: The progress bar will help track processing status for large email lists
- **Outdated Classifications**: Run without `--reuse-existing` to perform a full reclassification
- **Dictionary Not Applied**: Check that your MX dictionary file uses the correct format (suffix:category)

