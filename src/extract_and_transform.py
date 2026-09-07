import polars as pl

df = pl.read_csv("data/fifa21_raw_data.csv")

print(df.head())
print(df.schema)

df.drop("playerUrl")


# Convert weight in lbs to kg and height in feet to cm
df = df.with_columns(
    (pl.col("Weight").str.replace("lbs", "").cast(
        pl.Float64) / 2.2).round(0).cast(pl.Int32),
    ((pl.col("Height").str.extract(r"(\d+)", 1).cast(pl.Int32) * 12 +
      pl.col("Height").str.extract(r"'(\d+)", 1).cast(pl.Int32)) * 2.54).round(0).cast(pl.Int32)
)

# Split Team & Contract column into column for team, contract started year, contract ends year
# Split string Positions column into an an array of positions
df = df.with_columns(
    pl.col("Team & Contract").str.extract(
        r"~\s*(\d+)", 1).cast(pl.Int32).alias("Contract Ends"),
    pl.col("Team & Contract").str.extract(r"\s*(\d+)",
                                          1).cast(pl.Int32).alias("Contract Started"),
    pl.col("Team & Contract")
      .str.strip_chars()
      .str.split("\n")
      .list.first()
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
    pl.col("W/F").str.extract(r"(\d+)").cast(pl.Int32),
    pl.col("SM").str.extract(r"(\d+)").cast(pl.Int32),
    pl.col("IR").str.extract(r"(\d+)").cast(pl.Int32),
)

pl.col("Hits").str.strip_chars().cast(pl.Int32)
