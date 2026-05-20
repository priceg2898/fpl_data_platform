from shared.config.settings import get_settings

settings = get_settings()


def print_settings():
    settings = get_settings()
    print(settings)


if __name__ == "__main__":
    print_settings()
