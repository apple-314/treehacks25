import SwiftUI
import Contacts

class ContactManager: ObservableObject {
    @Published var allContacts: [CNContact] = []
    @Published var diffContacts: [CNContact] = []
    @Published var errorMessage: String?
    
    let comparisonContacts: [ContactComparison] = [
        ContactComparison(firstName: "Kaival", lastName: "Shah", phoneNumber: "9255949369"),
        ContactComparison(firstName: "David", lastName: "Lu", phoneNumber: "+16502729822"),
        ContactComparison(firstName: "James", lastName: "Chen", phoneNumber: "2032465757")
    ]
    
    func fetchAndCompareContacts() {
        let store = CNContactStore()
        
        store.requestAccess(for: .contacts) { [weak self] granted, error in
            guard let self = self else { return }
            
            if granted {
                let keys = [CNContactGivenNameKey, CNContactFamilyNameKey, CNContactPhoneNumbersKey]
                let request = CNContactFetchRequest(keysToFetch: keys as [CNKeyDescriptor])
                
                do {
                    var contacts: [CNContact] = []
                    try store.enumerateContacts(with: request) { contact, _ in
                        contacts.append(contact)
                    }
                    
                    DispatchQueue.main.async {
                        self.allContacts = contacts
                        self.findDifferences()
                    }
                } catch {
                    DispatchQueue.main.async {
                        self.errorMessage = "Error fetching contacts: \(error.localizedDescription)"
                    }
                }
            } else {
                DispatchQueue.main.async {
                    self.errorMessage = "Access to contacts denied"
                }
            }
        }
    }
    
    private func findDifferences() {
        let differentContacts = allContacts.filter { contact in
            !comparisonContacts.contains { comparisonContact in
                let phoneNumbers = contact.phoneNumbers.map {
                    self.normalizePhoneNumber($0.value.stringValue)
                }
                
                return contact.givenName.lowercased() == comparisonContact.firstName.lowercased() &&
                       contact.familyName.lowercased() == comparisonContact.lastName.lowercased() &&
                       phoneNumbers.contains(self.normalizePhoneNumber(comparisonContact.phoneNumber))
            }
        }
        
        diffContacts = differentContacts
    }
    
    private func normalizePhoneNumber(_ number: String) -> String {
        return number.replacingOccurrences(of: "[^0-9]", with: "", options: .regularExpression)
    }
}

// Model for comparison contacts
struct ContactComparison {
    let firstName: String
    let lastName: String
    let phoneNumber: String
}

struct ContentView: View {
    @StateObject private var contactManager = ContactManager()
    
    var body: some View {
        NavigationView {
            List {
                Section(header: Text("Different Contacts")) {
                    if contactManager.diffContacts.isEmpty {
                        Text("No differences found")
                            .foregroundColor(.gray)
                    } else {
                        ForEach(contactManager.diffContacts, id: \.identifier) { contact in
                            VStack(alignment: .leading) {
                                Text("\(contact.givenName) \(contact.familyName)")
                                    .font(.headline)
                                ForEach(contact.phoneNumbers, id: \.identifier) { phone in
                                    Text(phone.value.stringValue)
                                        .font(.subheadline)
                                        .foregroundColor(.gray)
                                }
                            }
                        }
                    }
                }
            }
            .navigationTitle("Contact Comparison")
            .alert("Error", isPresented: .constant(contactManager.errorMessage != nil)) {
                Button("OK") {
                    contactManager.errorMessage = nil
                }
            } message: {
                if let error = contactManager.errorMessage {
                    Text(error)
                }
            }
            .onAppear {
                contactManager.fetchAndCompareContacts()
            }
        }
    }
}

#Preview {
    ContentView()
}
