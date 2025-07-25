import dns.resolver
import argparse
from collections import defaultdict
import tqdm
import os

def get_mx_domains(email_domain):
    """Query MX records for an email domain"""
    try:
        answers = dns.resolver.resolve(email_domain, 'MX')
        # Sort by priority and return the highest priority MX domain
        return sorted([str(rdata.exchange).rstrip('.') for rdata in answers])
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
        return []

def load_mx_dict(dict_file):
    """Load MX dictionary from file"""
    mx_dict = {}
    try:
        with open(dict_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(':')
                if len(parts) == 2:
                    mx_suffix, category = parts
                    mx_dict[mx_suffix.strip()] = category.strip()
        return mx_dict
    except Exception as e:
        print(f"Error loading MX dictionary: {e}")
        return {}

def load_existing_classification(output_dir):
    """Load existing classification results"""
    existing = defaultdict(list)
    predefined_categories = ['Microsoft', 'Outlook', 'Gmail_Personal', 'Gmail_Enterprise']
    
    for category in predefined_categories:
        filename = category.replace('.', '_') + '.txt'
        file_path = os.path.join(output_dir, filename)
        
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                existing[category] = [line.strip() for line in f if line.strip()]
            print(f"Loaded {len(existing[category])} emails from existing {category} file")
    
    return existing

def classify_emails_by_mx(input_file, mx_dict=None, existing_classification=None):
    """Read email list and classify by MX records"""
    email_classification = defaultdict(list)
    email_mx_records = {}  # Store email:MX mapping for Other category
    
    # Use existing classification if provided
    if existing_classification:
        for category, emails in existing_classification.items():
            email_classification[category] = emails
    
    # Read all emails
    all_emails = set()
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            email = line.strip()
            if email:
                all_emails.add(email)
    
    # Determine emails that need classification (not in existing categories)
    classified_emails = set()
    for category_emails in email_classification.values():
        classified_emails.update(category_emails)
    
    emails_to_classify = sorted(all_emails - classified_emails)
    print(f"Found {len(emails_to_classify)} new emails to classify")
    
    # Show progress bar with tqdm
    for email in tqdm.tqdm(emails_to_classify, desc="Querying MX records"):
        # Extract email domain
        parts = email.split('@')
        if len(parts) != 2:
            print(f"Invalid email format: {email}")
            email_classification['invalid_format'].append(email)
            continue
            
        email_domain = parts[1]
        
        # Query MX records
        mx_domains = get_mx_domains(email_domain)
        if not mx_domains:
            email_classification['Other'].append(email)
            continue
            
        # Use the first MX domain as classification basis
        primary_mx = mx_domains[0]
        email_mx_records[email] = primary_mx
        
        # Special MX domain processing - Microsoft first
        domain_parts = primary_mx.split('.')
        if len(domain_parts) >= 4 and \
             domain_parts[-4] == 'mail' and \
             domain_parts[-3] == 'protection' and \
             domain_parts[-2] == 'outlook' and \
             domain_parts[-1] == 'com':
            category = 'Microsoft'
        elif len(domain_parts) >= 2 and domain_parts[-2] == 'outlook' and domain_parts[-1] == 'com':
            category = 'Outlook'
        elif len(domain_parts) >= 2 and domain_parts[-2] == 'google' and domain_parts[-1] == 'com':
            # Detailed Gmail classification
            if email_domain == 'gmail.com':
                category = 'Gmail_Personal'
            else:
                category = 'Gmail_Enterprise'
        else:
            # Check against MX dictionary if provided
            if mx_dict:
                for suffix, cat in mx_dict.items():
                    if primary_mx.endswith(suffix):
                        category = cat
                        break
                else:
                    category = 'Other'
            else:
                category = 'Other'
                
        email_classification[category].append(email)
    
    return email_classification, email_mx_records

def save_classification_results(results, email_mx_records, output_dir):
    """Save classification results to files"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    for category, emails in results.items():
        safe_filename = category.replace('.', '_') + '.txt'
        output_path = os.path.join(output_dir, safe_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for email in emails:
                if category == 'Other' and email in email_mx_records:
                    # Save Other category with MX record
                    f.write(f"{email}:{email_mx_records[email]}\n")
                else:
                    f.write(f"{email}\n")
                
        print(f"Saved {category} category ({len(emails)} emails) to {safe_filename}")

def reclassify_other_category(output_dir, mx_dict):
    """Reclassify emails in Other category using MX dictionary"""
    other_file = os.path.join(output_dir, 'Other.txt')
    if not os.path.exists(other_file):
        print("Other category file not found, skipping reclassification.")
        return
    
    reclassified = defaultdict(list)
    remaining = []
    
    with open(other_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
                
            parts = line.split(':')
            if len(parts) != 2:
                remaining.append(line)
                continue
                
            email, mx_domain = parts
            
            # Check against MX dictionary
            for suffix, category in mx_dict.items():
                if mx_domain.endswith(suffix):
                    reclassified[category].append(email)
                    break
            else:
                remaining.append(line)
    
    # Update classification results
    classification = defaultdict(list)
    for category in ['Microsoft', 'Outlook', 'Gmail_Personal', 'Gmail_Enterprise', 'Other']:
        filename = category.replace('.', '_') + '.txt'
        file_path = os.path.join(output_dir, filename)
        
        if category == 'Other':
            # Update Other category with remaining entries
            with open(file_path, 'w', encoding='utf-8') as f:
                for entry in remaining:
                    f.write(f"{entry}\n")
            classification[category] = [entry.split(':')[0] for entry in remaining]
        else:
            # Read existing category file
            existing_emails = []
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_emails = [line.strip() for line in f if line.strip()]
            
            # Add reclassified emails
            reclassified_emails = reclassified.get(category, [])
            all_emails = existing_emails + reclassified_emails
            
            # Write updated file
            with open(file_path, 'w', encoding='utf-8') as f:
                for email in all_emails:
                    f.write(f"{email}\n")
            
            classification[category] = all_emails
    
    # Print reclassification summary
    print("\nReclassification results:")
    for category, emails in reclassified.items():
        print(f"Moved {len(emails)} emails from Other to {category}")

def main():
    parser = argparse.ArgumentParser(description='Email MX Record Classifier')
    parser.add_argument('--input', required=True, help='Input email list file path')
    parser.add_argument('--output', default='classified_emails', help='Output directory path')
    parser.add_argument('--mx-dict', help='MX dictionary file path for secondary classification')
    parser.add_argument('--reuse-existing', action='store_true', help='Reuse existing classification results for predefined categories')
    args = parser.parse_args()
    
    print("Starting email MX record classification...")
    
    # Load MX dictionary if provided
    mx_dict = load_mx_dict(args.mx_dict) if args.mx_dict else {}
    
    # Load existing classification if requested
    existing_classification = None
    if args.reuse_existing:
        print("Checking for existing classification results...")
        existing_classification = load_existing_classification(args.output)
    
    # Primary classification
    classification, email_mx_records = classify_emails_by_mx(
        args.input, mx_dict, existing_classification
    )
    save_classification_results(classification, email_mx_records, args.output)
    
    # Secondary classification using MX dictionary
    if args.mx_dict:
        print("\nStarting secondary classification using MX dictionary...")
        reclassify_other_category(args.output, mx_dict)
    
    print("Classification completed!")

if __name__ == "__main__":
    # Make sure to install dnspython and tqdm libraries: pip install dnspython tqdm
    main()    
