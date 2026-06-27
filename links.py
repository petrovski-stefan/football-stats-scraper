def get_leagues_links() -> list[str]:
    with open("config/LEAGUES.txt") as f:
        return [line.strip().replace("\n", "") for line in f.readlines()]
