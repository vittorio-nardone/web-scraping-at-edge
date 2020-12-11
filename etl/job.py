import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.dynamicframe import DynamicFrame
from awsglue.job import Job

from pyspark.sql.window import Window
import pyspark.sql.functions as F

# Output bucket
bucket_name = 'your_bucket'

# Incoming data Glue database and table
glueContext = GlueContext(SparkContext.getOrCreate())
paradox_stream = glueContext.create_dynamic_frame.from_catalog(
             database="my-home",
             table_name="paradox_stream")

print("Count: {}".format(paradox_stream.count()))
paradox_stream.printSchema()

sensors_list = ['Soggiorno', 'Cucina', 'Bagno_Vittorio', 'Camera_Bambini', 'Bagno_Ospiti', 'Camera_Vittorio', 'Porta_Ingresso', 'Tamper_Sirena', 'Garage', 'Porta_Garage', 'Giardino_Bagno', 'Giardino_Cucina', 'Giardino_Sala', 'Taverna', 'Fumo_Garage']

df = paradox_stream.toDF()

# Cast to timestamp
df = df.withColumn("timestamp", F.to_timestamp("time", "yyyy/MM/dd HH:mm:ss")).drop('time')

# Remove dots in columns
def rename_cols(df):
    for column in df.columns:
        last_dot = column.rfind('.') 
        if last_dot >= 0:
            new_column = column[last_dot+1:]
            df = df.withColumnRenamed(column, new_column)
    return df
df = rename_cols(df)

# List of events
def events(df):
    w = Window().orderBy(F.col("timestamp").cast('long'))
    change_column = None

    for column in sensors_list:
        activation = F.col(column).cast("long") > F.lag(column, 1).over(w).cast("long")
        activation = F.when(activation, F.lit(' {}-UP'.format(column))).otherwise(F.lit(''))
        
        deactivation = F.col(column).cast("long") < F.lag(column, 1).over(w).cast("long")
        deactivation = F.when(deactivation, F.lit(' {}-DOWN'.format(column))).otherwise(F.lit(''))
        
        if change_column is not None:
            change_column = F.concat(change_column, activation, deactivation)
        else:
            change_column = F.concat(activation, deactivation)
            
    df = df.withColumn('event', F.trim(change_column)).drop(*sensors_list)
    df = df.withColumn('event', F.explode(F.split('event',' ')))
    return df
    
df2 = events(df)
dyf2 = DynamicFrame.fromDF(df2, glueContext, "paradox-events")
glueContext.write_dynamic_frame.from_options(frame = dyf2, connection_type = 's3', connection_options = {"path": "s3://{}/paradox-events".format(bucket_name)}, format="json")

# Find activation events vectors
timeout = 60 #seconds

w = Window().orderBy(F.col("timestamp").cast('long'))
begin_column = F.when(F.lag('timestamp', 1).over(w).isNull(), F.col('timestamp')).otherwise(F.when((F.col('timestamp').cast("long") - F.lag('timestamp', 1).over(w).cast("long")) > timeout, F.col('timestamp')))
df4 = df2.filter(F.col('event').contains('-UP')).withColumn('begin', begin_column)
df4 = df4.withColumn('begin', F.last('begin', True).over(w.rowsBetween(-sys.maxsize, 0)))
df4 = df4.groupBy('begin').agg(F.collect_list("event").alias('vector'))


dyf4 = DynamicFrame.fromDF(df4, glueContext, "paradox-vectors")
glueContext.write_dynamic_frame.from_options(frame = dyf4, connection_type = 's3', connection_options = {"path": "s3://{}/paradox-vectors".format(bucket_name)}, format="json")
