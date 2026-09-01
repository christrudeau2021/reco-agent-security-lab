from aim_sdk import secure

agent = secure("hello-agent", capabilities=["db:read"])


@agent.perform_action(capability="db:read")
def get_customer(customer_id):
    return {"id": customer_id, "name": "demo-corp customer"}


if __name__ == "__main__":
    print(get_customer("cust-001"))
