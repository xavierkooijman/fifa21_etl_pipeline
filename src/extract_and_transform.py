import polars as pl
pl.Config.set_fmt_str_lengths(100)
df = pl.read_csv("data/fifa21_raw_data.csv")

print(df.head())
print(df.schema)


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
    pl.when(pl.col("Team & Contract").str.contains("On Loan|Free"))
    .then(None)
    .otherwise(
        pl.col("Team & Contract")
        .str.extract(r"\s*(\d+)", 1)
        .cast(pl.Int32)
    )
    .alias("Contract Started"),
    pl.when(pl.col("Team & Contract").str.contains("On Loan|Free"))
    .then(None)
    .otherwise(
        pl.col("Team & Contract")
        .str.extract(r"~\s*(\d+)", 1)
        .cast(pl.Int32)
    )
    .alias("Contract Ends"),
    pl.when(pl.col("Team & Contract").str.contains("Free"))
    .then(None)
    .otherwise(
        pl.col("Team & Contract")
        .str.split("\n")
        .list.first()
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
        pl.col("Hits").str.extract(r"(\d+(?:\.\d+)?)").cast(pl.Float32) * 1000
    )
    .otherwise(
        pl.col("Hits").str.extract(r"(\d+(?:\.\d+)?)").cast(pl.Float32)
    ).cast(pl.Int32),
    pl.when(pl.col("Value").str.ends_with("K"))
    .then(
        pl.col("Value").str.extract(r"(\d+(?:\.\d+)?)").cast(pl.Float32) * 1000
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
        pl.col("Wage").str.extract(r"(\d+(?:\.\d+)?)").cast(pl.Float32) * 1000
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
