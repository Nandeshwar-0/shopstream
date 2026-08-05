from ingestion.extractor import IncrementalExtractor

def main():
    print("Starting incremental extraction pipeline...")
    
    # Core tables to extract
    tables_to_extract = [
        "customers",
        "products",
        "orders",
        "order_items",
        "payments",
        "shipping",
        "inventory",
        "reviews"
    ]
    
    total_extracted = 0
    for table in tables_to_extract:
        extractor = IncrementalExtractor(table_name=table)
        try:
            rows = extractor.extract()
            total_extracted += rows
        except Exception as e:
            print(f"Error extracting {table}: {e}")
            
    print(f"Extraction complete! Total rows incrementally extracted: {total_extracted}")

if __name__ == "__main__":
    main()
