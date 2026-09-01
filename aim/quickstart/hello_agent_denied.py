from aim_sdk import secure

agent = secure("hello-agent", capabilities=["db:read"])


@agent.perform_action(capability="finance:wire_transfer", auto_register=False)
def wire_transfer(customer_id, amount):
    return {"id": customer_id, "wired": amount}


if __name__ == "__main__":
    print(wire_transfer("cust-001", 500))
