"""
model for lmabda
"""
from datetime import datetime
from os import getenv
from pytz import UTC
from pynamodb.attributes import (
		MapAttribute,
		UnicodeAttribute, UTCDateTimeAttribute, BooleanAttribute
)
from pynamodb.models import Model

from constants import ENV, AWS_REGION

# Copy-pasting this function from utils to prevent ImportError (Circular imports)
def get_now():	
	"""
	get current datetime in UTC
	"""
	return datetime.utcnow().replace(tzinfo=UTC)

def create_table_name(table_name):
		"""
		create table to name for dynamodb
		"""
		return '%s-%s' % (ENV, table_name)


class ShortURL(Model):
	"""
	A DynamoDB VideoWatch
	"""

	class Meta:
		"""
		set meta of table
		"""
		table_name = create_table_name("el-chapo-short-url-store")
		region = getenv("environ")

	url = UnicodeAttribute(hash_key=True, null=False)
	redirection_url = UnicodeAttribute(null=False)
	webhook = UnicodeAttribute(null=True)
	created_at = UTCDateTimeAttribute(default=get_now())


# automatically creates a table in dynamo db if doesnt exist.
if not ShortURL.exists():
	ShortURL.create_table(wait=True, billing_mode="PAY_PER_REQUEST")

# A DynamoDB Model for request logging
class RequestLogger(Model):
	"""A DynamoDB collection for logging request metadata for every request"""
	class Meta:
		# Setting the meta explicitly for testing purposes.
		table_name = 'elchapo_request_logger'
		region = getenv("AWS_REGION")
		# Add this to prevent table creation errors on AWS DynamoDB
		billing_mode = 'PAY_PER_REQUEST'
	
	# Attributes part of the model
	short_url = UnicodeAttribute(attr_name="Associated short URL", hash_key=True)
	request=MapAttribute(attr_name="Request data")
	timestamp = UTCDateTimeAttribute(default=get_now(), range_key=True)

# Create the table if it does not exist
if not RequestLogger.exists():
	RequestLogger.create_table(wait=True, billing_mode="PAY_PER_REQUEST")