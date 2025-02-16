import SwiftUI
import Contacts

struct ContactButton: View {
    let color: Color
    let size: CGFloat = 100
    let onTap: () -> Void
    
    var body: some View {
        Circle()
            .fill(color)
            .frame(width: size, height: size)
            .overlay(
                Circle()
                    .stroke(Color.white, lineWidth: 2)
            )
            .shadow(radius: 5)
            .onTapGesture {
                onTap()
            }
    }
}

class ContactManager: ObservableObject {
    @Published var firstContactList: [CNContact] = []
    @Published var secondContactList: [CNContact] = []
    @Published var diffContacts: [CNContact] = []
    @Published var errorMessage: String?
    @Published var statusMessage: String = "Tap green button for first capture"
    
    func fetchContacts(isFirstCapture: Bool) {
        if isFirstCapture {
            print("DEBUG: Green button tapped - capturing first list")
        } else {
            print("DEBUG: Red button tapped - capturing second list and comparing")
        }
        
        let store = CNContactStore()
        
        store.requestAccess(for: .contacts) { [weak self] granted, error in
            guard let self = self else { return }
            
            if granted {
                let keys = [CNContactGivenNameKey, CNContactFamilyNameKey, CNContactPhoneNumbersKey, CNContactEmailAddressesKey]
                let request = CNContactFetchRequest(keysToFetch: keys as [CNKeyDescriptor])
                
                do {
                    var contacts: [CNContact] = []
                    try store.enumerateContacts(with: request) { contact, _ in
                        contacts.append(contact)
                    }
                    
                    DispatchQueue.main.async {
                        if isFirstCapture {
                            self.firstContactList = contacts
                            print("DEBUG: First capture complete - \(contacts.count) contacts stored")
                            self.statusMessage = "First capture complete. Tap red button for second capture."
                        } else {
                            self.secondContactList = contacts
                            print("DEBUG: Second capture complete - comparing lists now")
                            self.findDifferences()
                        }
                    }
                } catch {
                    DispatchQueue.main.async {
                        self.errorMessage = "Error fetching contacts: \(error.localizedDescription)"
                    }
                }
            }
        }
    }
    
    private func findDifferences() {
        print("DEBUG: Starting comparison between \(firstContactList.count) and \(secondContactList.count) contacts")
        
        let differentContacts = secondContactList.filter { contact2 in
            !firstContactList.contains { contact1 in
                let phones1 = contact1.phoneNumbers.map { normalizePhoneNumber($0.value.stringValue) }
                let phones2 = contact2.phoneNumbers.map { normalizePhoneNumber($0.value.stringValue) }
                
                let contact1Emails = contact1.emailAddresses.map { ($0.value as String).lowercased() }
                let contact2Emails = contact2.emailAddresses.map { ($0.value as String).lowercased() }

                return contact1.givenName.lowercased() == contact2.givenName.lowercased() &&
                       contact1.familyName.lowercased() == contact2.familyName.lowercased() &&
                       !Set(phones1).isDisjoint(with: Set(phones2)) &&
                       !Set(contact1Emails).isDisjoint(with: Set(contact2Emails))

            }
        }
        
        diffContacts = differentContacts
        print("DEBUG: Comparison complete - found \(differentContacts.count) new contacts")
        
        // Print each new contact found
        differentContacts.forEach { contact in
            print("DEBUG: New contact: \(contact.givenName) \(contact.familyName)")
            contact.phoneNumbers.forEach { phone in
                print("DEBUG: - Phone: \(phone.value.stringValue)")
            }
            contact.emailAddresses.forEach { email in
                print("DEBUG: - Email: \(email.value as String)")
            }
        }
        
        statusMessage = "Comparison complete. Found \(differentContacts.count) new contacts."
    }
    
    private func normalizePhoneNumber(_ number: String) -> String {
        return number.replacingOccurrences(of: "[^0-9]", with: "", options: .regularExpression)
    }
}

struct ContentView: View {
    @StateObject private var contactManager = ContactManager()
    
    var body: some View {
        NavigationView {
            VStack {
                Text(contactManager.statusMessage)
                    .padding()
                    .multilineTextAlignment(.center)
                
                HStack(spacing: 40) {
                    VStack {
                        Text("First Capture")
                            .font(.caption)
                        ContactButton(color: .green) {
                            contactManager.fetchContacts(isFirstCapture: true)
                        }
                    }
                    
                    VStack {
                        Text("Second Capture")
                            .font(.caption)
                        ContactButton(color: .red) {
                            contactManager.fetchContacts(isFirstCapture: false)
                        }
                    }
                }
                .padding()
                
                List {
                    Section(header: Text("New Contacts Found")) {
                        if contactManager.diffContacts.isEmpty {
                            Text("No differences found")
                                .foregroundColor(.gray)
                        } else {
                            ForEach(contactManager.diffContacts, id: \.identifier) { contact in
                                VStack(alignment: .leading) {
                                    Text("\(contact.givenName) \(contact.familyName)")
                                        .font(.headline)
                                    ForEach(contact.phoneNumbers, id: \.identifier) { phone in
                                        Text("📱 \(phone.value.stringValue)")
                                            .font(.subheadline)
                                            .foregroundColor(.gray)
                                    }
                                    ForEach(contact.emailAddresses, id: \.identifier) { email in
                                        Text("✉️ \(email.value as String)")
                                            .font(.subheadline)
                                            .foregroundColor(.gray)
                                    }
                                }
                            }
                        }
                    }
                }
            }
            .navigationTitle("Contact Changes")
            .alert("Error", isPresented: .constant(contactManager.errorMessage != nil)) {
                Button("OK") {
                    contactManager.errorMessage = nil
                }
            } message: {
                if let error = contactManager.errorMessage {
                    Text(error)
                }
            }
        }
        .onAppear {
            contactManager.fetchContacts(isFirstCapture: true)
        }
    }
}

#Preview {
    ContentView()
}

