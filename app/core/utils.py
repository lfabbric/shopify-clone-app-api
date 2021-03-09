def comma_splitter(tag_string):
    return [t.strip().lower() for t in tag_string.split(',') if t.strip()]
