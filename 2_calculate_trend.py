from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode, split, lower, date_format, lag, window, unix_timestamp
from pymongo import MongoClient
import argparse
import config
from bson import json_util
import spacy
from spacy_udpipe import load, download
from pyspark.sql import Row
from pyspark.sql.functions import length

from pyspark.sql.functions import expr


client = None
spark = None

# Load SpaCy in Dutch
# python -m spacy download nl_core_news_sm
nlp = spacy.load("nl_core_news_sm")
download("nl")


def create_client(mongo_server):
    global client
    if not client:
        client = MongoClient(host=[mongo_server])


def extract_data_mongodb(database, collection, **kwargs):
    data = []
    with MongoClient(host=[mongo_server]) as client:
        db = client[database]
        col = db[collection]
        data = list(col.find({}))
    return data


def create_spark_dataframe(data):
    global spark
    spark = SparkSession.builder \
        .appName("TwitterTrending") \
        .config("spark.executor.memory", "4g") \
        .config("spark.driver.memory", "4g") \
        .config("spark.sql.legacy.timeParserPolicy", "LEGACY") \
        .config("spark.sql.files.maxPartitionBytes", "128m") \
        .getOrCreate()
    json_data = [json_util.dumps(doc) for doc in data]
    df = (spark.read
          .option("allowUnquotedFieldNames", "true")
          .json(spark.sparkContext.parallelize(json_data, numSlices=10), multiLine=True))
    return df


def extract_nouns(iter):
    nlp = spacy.load("nl_core_news_sm")
    for row in iter:
        text = row.text
        doc = nlp(text)
        nouns = [token.text for token in doc if token.pos_ == "NOUN"]
        for noun in nouns:
            yield Row(created_at=row.created_at, word=noun)


def calculate_trend(df_data):
    # All tweets are in Dutch -> db.getCollection('twitter-sample').distinct("language.tag")

    # 1) Filter out myspace, digg and facebook interactions
    twitter_data = df_data.filter(col("interaction.type") == "twitter").limit(100)

    # 2-) Differentiate between tweet or retweet
    is_retweet = twitter_data.withColumn("is_retweet", col("twitter.retweet").isNotNull())
    retweets = is_retweet.filter(col("is_retweet") == True)
    tweets = is_retweet.filter(col("is_retweet") == False)

    # 3-) Split tweet content by words
    words = tweets.select(
        unix_timestamp(col("twitter.created_at"), "EEE, dd MMM yyyy HH:mm:ss Z").cast("timestamp").alias("created_at"),
        col("twitter.text").alias("text")
    )

    # 4-) Extract nouns and filter stop words
    result_rdd = words.rdd.mapPartitions(lambda iter: extract_nouns(iter))
    filtered_nouns_df = spark.createDataFrame(result_rdd, schema=["created_at", "word"])

    # 5-) Group tweets by time intervals (7 days)
    word_counts = filtered_nouns_df.groupBy(window("created_at", "7 day"), "word").count()

    # 6-) Filter out words with < 1 character
    filtered_word_counts = word_counts.filter(length(col("word")) > 1)

    # 7-) Calculate trend
    word_trends = filtered_word_counts.withColumn(
        "trend_slope",
        col("count").cast("double") / col("window").getField("end").cast("double"))

    # 8-) Save dataset as csv
    word_trends.orderBy("trend_slope", ascending=False).show(truncate=False)
    result_df = word_trends.select("window.start", "window.end", "word", "count", "trend_slope")
    result_df.write.csv("twitter_trend_output", header=True, mode="overwrite")


def parse_args():
    parser = argparse.ArgumentParser(description='Extract datasets.')
    parser.add_argument('database', type=str, help='The name of the database to extract.')
    parser.add_argument('collection', type=str, help='The name of the collection to extract.')
    parser.add_argument('-verbose', '-v', dest='verbose', action='store_true', default=False,
                        help='Show some output while work is being done.')
    return parser.parse_args()


def main():
    create_client(mongo_server)
    json_data = extract_data_mongodb(**vars(parse_args()))
    df_data = create_spark_dataframe(json_data)
    calculate_trend(df_data)
    spark.stop()
    client.close()


if __name__ == '__main__':
    c = config.config()
    mongo_server = c.readh('mongodb', 'server') or 'localhost'

    main()
