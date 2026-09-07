import polars as pl

df = pl.read_csv("data/fifa21_raw_data.csv")

print(df.head())
print(df.schema)

df.drop("playerUrl")

df = df.with_columns(
    (pl.col("Weight").str.replace("lbs", "").cast(
        pl.Float64) / 2.2).round(0).cast(pl.Int32)
)

df = df.with_columns(
    ((pl.col("Height").str.extract(r"(\d+)", 1).cast(pl.Int32) * 12 +
     pl.col("Height").str.extract(r"'(\d+)", 1).cast(pl.Int32)) * 2.54).round(0).cast(pl.Int32)
)


df = df.with_columns(
    pl.col("Team & Contract").str.extract(
        r"~\s*(\d+)", 1).cast(pl.Int32).alias("Contract Ends")
)

df = df.with_columns(
    pl.col("Team & Contract").str.extract(r"\s*(\d+)",
                                          1).cast(pl.Int32).alias("Contract Started")
)

df = df.with_columns(
    pl.col("Team & Contract")
      .str.strip_chars()
      .str.split("\n")
      .list.first()
      .alias("Team")
)

df = df.drop("Team & Contract")

df = df.with_columns(
    pl.col("Loan Date End").replace(
        "N/A", None).str.strptime(pl.Date, "%b %d, %Y", strict=False)
)

df = df.with_columns(
    pl.col("Joined").str.strptime(pl.Date, "%b %d, %Y", strict=False)
)
