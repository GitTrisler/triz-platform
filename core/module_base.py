class TRIZModule:
    name = "Unnamed Module"
    category = "General"
    description = ""
    accent = "#38BDF8"

    def create_page(self):
        raise NotImplementedError("Module must implement create_page().")
