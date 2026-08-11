from core.autocad import acad

print("=" * 60)

print("pywin32 available:", acad.is_available())

if acad.connect():

    print("\nConnected Successfully\n")

    print("Application Name:")
    print(getattr(acad.app, "Name", "<None>"))

    print("\nApplication Caption:")
    print(getattr(acad.app, "Caption", "<None>"))

    print("\nVersion:")
    print(getattr(acad.app, "Version", "<None>"))

    print("\nVisible:")
    print(getattr(acad.app, "Visible", "<None>"))

    print("\nDocuments Count:")

    try:
        print(acad.app.Documents.Count)

        for i in range(acad.app.Documents.Count):
            doc = acad.app.Documents.Item(i)

            print("--------------------------------")

            print("Name:", doc.Name)
            print("FullName:", doc.FullName)
            print("Active Layout:", doc.ActiveLayout.Name)

    except Exception as e:
        print(e)

    print("\nActiveDocument:")

    try:
        doc = acad.app.ActiveDocument

        print(doc)
        print("Name:", doc.Name)
        print("Layout:", doc.ActiveLayout.Name)

    except Exception as e:
        print(e)

else:

    print(acad.get_state().error)
