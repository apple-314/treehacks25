import SwiftUI
import Contacts

struct ContentView: View {
    @State private var permissionStatus: String = "Not Requested"
    @State private var contacts: [CNContact] = []
    private let contactStore = CNContactStore()
    
    var body: some View {
        VStack(spacing: 20) {
            Text("Vision Pro Contact Access")
                .font(.title)
            
            Text("Status: \(permissionStatus)")
                .padding()
            
            if !contacts.isEmpty {
                ScrollView {
                    VStack(alignment: .leading, spacing: 10) {
                        ForEach(contacts, id: \.identifier) { contact in
                            Text("\(contact.givenName) \(contact.familyName)")
                                .padding(.horizontal)
                        }
                    }
                }
                .frame(maxHeight: 300)
            }
        }
        .padding()
        .background(.clear)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .onAppear {
            requestContactsPermission()
        }
    }
    
    private func requestContactsPermission() {
        contactStore.requestAccess(for: .contacts) { granted, error in
            DispatchQueue.main.async {
                if let error = error {
                    permissionStatus = "Error: \(error.localizedDescription)"
                } else if granted {
                    permissionStatus = "Granted"
                    fetchContacts()
                } else {
                    permissionStatus = "Denied"
                }
            }
        }
    }
    
    private func fetchContacts() {
        let keys = [CNContactGivenNameKey, CNContactFamilyNameKey]
        let request = CNContactFetchRequest(keysToFetch: keys as [CNKeyDescriptor])
        
        do {
            var fetchedContacts: [CNContact] = []
            try contactStore.enumerateContacts(with: request) { contact, stop in
                fetchedContacts.append(contact)
                print("Contact: \(contact.givenName) \(contact.familyName)")
            }
            self.contacts = fetchedContacts
        } catch {
            print("Error fetching contacts: \(error)")
            permissionStatus = "Error fetching contacts: \(error.localizedDescription)"
        }
    }
}

#Preview {
    ContentView()
}
