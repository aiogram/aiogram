import factory

id_ = factory.Sequence(lambda n: n)
first_name = factory.Sequence(lambda n: f"First name #{n}")
last_name = factory.Sequence(lambda n: f"Last name #{n}")
username = factory.Sequence(lambda n: f"Username #{n}")
