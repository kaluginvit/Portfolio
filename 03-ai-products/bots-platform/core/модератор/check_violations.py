import modal

app = modal.App("check-violations")

@app.local_entrypoint()
def main():
    violations_dict = modal.Dict.from_name("moderator-violations", create_if_missing=False)
    all_data = dict(violations_dict)
    print("Все нарушения:", all_data)
    user_id = "1770409440"
    print(f"User {user_id}: {all_data.get(user_id, 0)} нарушений")
