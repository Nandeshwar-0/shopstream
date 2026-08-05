import sys
from data_generator.generators import ShopStreamGenerator
from data_generator.db import PostgresClient

def get_count():
    with PostgresClient() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT COUNT(*) as count FROM orders')
            return cur.fetchone()['count']

def main():
    generator = ShopStreamGenerator()
    while True:
        count = get_count()
        print(f"Current order count: {count}")
        if count >= 1000:
            print("Reached 1000+ orders. Done!")
            break
        print("Generating more orders...")
        generator.run_seed()

if __name__ == '__main__':
    main()
