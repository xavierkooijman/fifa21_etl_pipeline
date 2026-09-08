import polars as pl
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def extract_and_transform():

    df = pl.read_csv(DATA_DIR / "fifa21_raw_data.csv")

    df = df.drop("playerUrl")
    df = df.with_columns(
        pl.col(pl.String)
        .str.strip_chars()
    )

    # Convert weight in lbs to kg and height in feet to cm
    df = df.with_columns(
        (pl.col("Weight").str.extract(r"(\d+)").cast(
            pl.Float64) / 2.2).round(0).cast(pl.Int32),
        ((pl.col("Height").str.extract(r"(\d+)", 1).cast(pl.Int32) * 12 +
          pl.col("Height").str.extract(r"'(\d+)", 1).cast(pl.Int32)) * 2.54).round(0).cast(pl.Int32)
    )

    # Split Team & Contract column into column for team, contract started year, contract ends year
    # Split string Positions column into an an array of positions
    df = df.with_columns(
        pl.col("Team & Contract")
        .str.replace(r"^\s*\d+\.\s*", "")
    )

    df = df.with_columns(
        pl.when(pl.col("Team & Contract").str.contains("On Loan|Free"))
        .then(None)
        .otherwise(
            pl.col("Team & Contract")
            .str.extract(r"(\d{4})\s*~", 1)
            .cast(pl.Int32)
        )
        .alias("Contract Started"),
        pl.when(pl.col("Team & Contract").str.contains("On Loan|Free"))
        .then(None)
        .otherwise(
            pl.col("Team & Contract")
            .str.extract(r"~\s*(\d{4})", 1)
            .cast(pl.Int32)
        )
        .alias("Contract Ends"),
        pl.when(pl.col("Team & Contract").str.contains("Free"))
        .then(None)
        .when(pl.col("Team & Contract").str.contains("On Loan"))
        .then(
            pl.col("Team & Contract")
            .str.replace(r"\s+[A-Z][a-z]{2} \d{1,2}, \d{4} On Loan$", "")
        )
        .otherwise(
            pl.col("Team & Contract").str.replace(
                r"\s+\d{4}\s*~\s*\d{4}\s*$", "")
        )
        .alias("Team"),
        pl.col("Positions").str.split(" ")
    )

    df = df.drop("Team & Contract")

    # Cast string columns to date
    df = df.with_columns(
        pl.col("Loan Date End").replace(
            "N/A", None).str.strptime(pl.Date, "%b %d, %Y", strict=False),
        pl.col("Joined").str.strptime(pl.Date, "%b %d, %Y", strict=False)

    )

    # Get only digits, no stars and cast to integer
    df = df.with_columns(
        pl.col("W/F").str.extract(r"(\d)").cast(pl.Int32),
        pl.col("SM").str.extract(r"(\d)").cast(pl.Int32),
        pl.col("IR").str.extract(r"(\d)").cast(pl.Int32),
    )

    # Strip euro sign, Calculate Value, Wage, Release Clause and Hits based on if it ends in M(million) or K(thousand)
    df = df.with_columns(
        pl.col("Value", "Wage", "Release Clause").str.replace_all("€", "")
    )

    df = df.with_columns(
        pl.when(pl.col("Hits").str.ends_with("K"))
        .then(
            pl.col("Hits").str.extract(
                r"(\d+(?:\.\d+)?)").cast(pl.Float32) * 1000
        )
        .otherwise(
            pl.col("Hits").str.extract(r"(\d+(?:\.\d+)?)").cast(pl.Float32)
        ).cast(pl.Int32),
        pl.when(pl.col("Value").str.ends_with("K"))
        .then(
            pl.col("Value").str.extract(
                r"(\d+(?:\.\d+)?)").cast(pl.Float32) * 1000
        )
        .when(pl.col("Value").str.ends_with("M"))
        .then(
            pl.col("Value").str.extract(
                r"(\d+(?:\.\d+)?)").cast(pl.Float32) * 1000000
        )
        .otherwise(
            pl.col("Value").str.extract(r"(\d+(?:\.\d+)?)").cast(pl.Float32)
        ).cast(pl.Int32),
        pl.when(pl.col("Wage").str.ends_with("K"))
        .then(
            pl.col("Wage").str.extract(
                r"(\d+(?:\.\d+)?)").cast(pl.Float32) * 1000
        )
        .when(pl.col("Wage").str.ends_with("M"))
        .then(
            pl.col("Wage").str.extract(
                r"(\d+(?:\.\d+)?)").cast(pl.Float32) * 1000000
        )
        .otherwise(
            pl.col("Wage").str.extract(r"(\d+(?:\.\d+)?)").cast(pl.Float32)
        ).cast(pl.Int32),
        pl.when(pl.col("Release Clause").str.ends_with("K"))
        .then(
            pl.col("Release Clause").str.extract(
                r"(\d+(?:\.\d+)?)").cast(pl.Float32) * 1000
        )
        .when(pl.col("Release Clause").str.ends_with("M"))
        .then(
            pl.col("Release Clause").str.extract(
                r"(\d+(?:\.\d+)?)").cast(pl.Float32) * 1000000
        )
        .otherwise(
            pl.col("Release Clause").str.extract(
                r"(\d+(?:\.\d+)?)").cast(pl.Float32)
        ).cast(pl.Int32),
    )

    # renaming total columns to know which ones are derived sums of other columns
    df = df.rename({
        "Attacking": "Total Attacking",
        "Skill": "Total Skill",
        "Movement": "Total Movement",
        "Power": "Total Power",
        "Mentality": "Total Mentality",
        "Defending": "Total Defending",
        "Goalkeeping": "Total Goalkeeping",
        "Base Stats": "Total Base Stats",
        "↓OVA": "OVA"
    })

    # mentality is missing a column(Attack position), must calculate total mentality based on existing columns. Same for total stats.
    df = df.drop("Total Mentality")
    mentality_cols = [
        "Aggression",
        "Interceptions",
        "Positioning",
        "Vision",
        "Penalties",
        "Composure"
    ]
    df = df.with_columns(
        pl.sum_horizontal(mentality_cols).alias("Total Mentality")
    )

    df = df.drop("Total Stats")
    stats_cols = [
        "Total Attacking",
        "Total Skill",
        "Total Movement",
        "Total Mentality",
        "Total Defending",
        "Total Goalkeeping"
    ]
    df = df.with_columns(
        pl.sum_horizontal(stats_cols).alias("Total Stats")
    )

    return df
