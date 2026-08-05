from __future__ import annotations

from .generators import ShopStreamGenerator


def main() -> None:
    generator = ShopStreamGenerator()
    generator.run_seed()
    print("ShopStream synthetic data generation completed.")


if __name__ == "__main__":
    main()
