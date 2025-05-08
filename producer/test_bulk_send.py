from data_generator import generate_bulk_data
from producer import publish_message

for msg in generate_bulk_data(100):
    publish_message(msg)
