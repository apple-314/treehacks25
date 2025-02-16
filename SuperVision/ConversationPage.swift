import SwiftUI
import AVFoundation
import Contacts

// MARK: - ContactButton
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

// MARK: - ContactManager
class ContactManager: ObservableObject {
    @Published var firstContactList: [CNContact] = []
    @Published var secondContactList: [CNContact] = []
    @Published var diffContacts: [CNContact] = []
    @Published var errorMessage: String?
    @Published var statusMessage: String = "Tap green button for first capture"
    
    func fetchContacts(isFirstCapture: Bool) async throws {
        if isFirstCapture {
            print("DEBUG: Green button tapped - capturing first list")
        } else {
            print("DEBUG: Red button tapped - capturing second list and comparing")
        }
        
        let store = CNContactStore()
        let granted = try await store.requestAccess(for: .contacts)
        guard granted else {
            throw NSError(domain: "ContactManagerError", code: 1, userInfo: [NSLocalizedDescriptionKey: "Access to contacts was not granted"])
        }
        
        let keys = [CNContactGivenNameKey, CNContactFamilyNameKey, CNContactPhoneNumbersKey, CNContactEmailAddressesKey]
        let request = CNContactFetchRequest(keysToFetch: keys as [CNKeyDescriptor])
        
        var contacts: [CNContact] = []
        try store.enumerateContacts(with: request) { contact, _ in
            contacts.append(contact)
        }
        
        if isFirstCapture {
            self.firstContactList = contacts
            print("DEBUG: First capture complete - \(contacts.count) contacts stored")
            try await sendContactsCount(with: "first: " + String(self.firstContactList.count))
            self.statusMessage = "First capture complete. Tap red button for second capture."
        } else {
            self.secondContactList = contacts
            print("DEBUG: Second capture complete - comparing lists now")
            try await sendContactsCount(with: "second: " + String(self.secondContactList.count))
            
            var contactDifferences: [String] = []
            for secondContact in self.secondContactList {
                var didFindMatch = false
                for firstContact in self.firstContactList {
                    if secondContact.givenName == firstContact.givenName {
                        didFindMatch = true
                    }
                }
                if !didFindMatch {
                    contactDifferences.append(secondContact.givenName)
                    contactDifferences.append(secondContact.familyName)
                    try await saveContact(firstName: secondContact.givenName, lastName: secondContact.familyName, phoneNumber: secondContact.normalizedPhoneNumbers.first ?? "")
                }
            }
            
            // Send the contact differences and wait for completion
            try await sendName(with: contactDifferences.joined(separator: ", "))
        }
    }
    
    private func sendContactsCount(with body: String) {
        let contactsCountString = "https://normal-guiding-orca.ngrok-free.app/count_contacts"
        guard let url = URL(string: contactsCountString) else {
            print("Invalid contactsCount URL.")
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("text/plain", forHTTPHeaderField: "Content-Type")
        request.httpBody = body.data(using: .utf8)
        
        let task = URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                print("Error sending contacts count: \(error)")
            } else {
                print("Contacts count sent.")
            }
        }
        task.resume()
    }

    private func saveContact(firstName: String, lastName: String, phoneNumber: String) async throws {
        let endpoint = "https://normal-guiding-orca.ngrok-free.app/save_contact"
        guard let url = URL(string: endpoint) else {
            throw URLError(.badURL)
        }
        
        // Create a JSON payload with the provided contact details
        let payload: [String: String] = [
            "firstName": firstName,
            "lastName": lastName,
            "phoneNumber": phoneNumber
        ]
        
        // Convert the payload dictionary to JSON data
        let jsonData = try JSONSerialization.data(withJSONObject: payload, options: [])
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = jsonData
        
        let (_, response) = try await URLSession.shared.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }
    }

    
    private func sendName(with body: String) async throws {
        let contactsCountString = "https://normal-guiding-orca.ngrok-free.app/obtain_name"
        guard let url = URL(string: contactsCountString) else {
            throw URLError(.badURL)
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("text/plain", forHTTPHeaderField: "Content-Type")
        request.httpBody = body.data(using: .utf8)
        
        let (_, response) = try await URLSession.shared.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }
    }

    private func sendDifferentContactsNames(_ contacts: [CNContact]) {
        let contactsCountString = "https://normal-guiding-orca.ngrok-free.app/count_contacts"
        let names = contacts.map { "\($0.givenName) \($0.familyName)" }
        let jsonPayload: [String: Any] = ["contacts": names]
        
        guard let url = URL(string: contactsCountString) else {
            print("Invalid contactsCount URL.")
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        do {
            let data = try JSONSerialization.data(withJSONObject: jsonPayload, options: [])
            request.httpBody = data
        } catch {
            print("Error converting contacts names to JSON: \(error)")
            return
        }
        
        let task = URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                print("Error sending different contacts names: \(error)")
            } else {
                print("Different contacts names sent.")
            }
        }
        task.resume()
    }
    
    func normalizePhoneNumber(_ phone: String) -> String {
        let digits = phone.filter { $0.isWholeNumber }
        if digits.count == 11 && digits.first == "1" {
            return String(digits.dropFirst())
        }
        if digits.count > 10 {
            return String(digits.suffix(10))
        }
        return digits
    }
}

// MARK: - API Response Models
struct Profile: Codable {
    let name: String
    let about: String
    let education: [[String]]
    let experiences: [[String]]
    let profile_url: String
        
    var educationText: String {
        education.map { $0.joined(separator: " - ") }.joined(separator: "\n")
    }
    
    var experiencesText: String {
        experiences.map { $0.joined(separator: " - ") }.joined(separator: "\n")
    }
}

struct CaptureResponse: Codable {
    let message: String
    let screenshot: String
    let profile: Profile
}

// MARK: - AudioProcessor (with custom endpoint support and finalize callback)
class AudioProcessor: ObservableObject {
    private var audioEngine = AVAudioEngine()
    private var inputNode: AVAudioInputNode?
    private var audioFormat: AVAudioFormat?
    private var isAudioSessionConfigured = false
    private var audioFile: AVAudioFile?
    private var fileURL: URL?
    
    @Published var isRecording = false
    @Published var audioLevel: Float = 0.0
    
    private let uploadURLString: String
    private let finalizeString: String
    
    /// Optional callback that is called when finalizeSamples() gets a response.
    var onFinalize: ((String, String) -> Void)?
    
    /// Initialize with custom endpoints. The default endpoints are used if none are provided.
    init(uploadEndpoint: String = "https://normal-guiding-orca.ngrok-free.app/upload_samples",
         finalizeEndpoint: String = "https://normal-guiding-orca.ngrok-free.app/finalize") {
        self.uploadURLString = uploadEndpoint
        self.finalizeString = finalizeEndpoint
    }
    
    func setupAudioSession() {
        let session = AVAudioSession.sharedInstance()
        do {
            try session.setCategory(.playAndRecord,
                                    mode: .default,
                                    options: [.defaultToSpeaker, .allowBluetooth])
            try session.setActive(true)
            isAudioSessionConfigured = true
        } catch {
            print("Failed to set up audio session: \(error)")
        }
    }
    
    func startRecording() {
        guard isAudioSessionConfigured else { return }
        
        let engine = audioEngine
        let inputNode = engine.inputNode
        let format = inputNode.outputFormat(forBus: 0)
        
        self.inputNode = inputNode
        self.audioFormat = format
        
        // Optional: saving to file (if needed)
        let directory = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let fileName = "recording.wav"
        let fileURL = directory.appendingPathComponent(fileName)
        self.fileURL = fileURL
        
        do {
            if FileManager.default.fileExists(atPath: fileURL.path) {
                try FileManager.default.removeItem(at: fileURL)
            }
            audioFile = try AVAudioFile(forWriting: fileURL,
                                        settings: format.settings,
                                        commonFormat: .pcmFormatFloat32,
                                        interleaved: false)
            print("Audio file will be saved at: \(fileURL.path)")
        } catch {
            print("Error creating audio file: \(error)")
            return
        }
        
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: format) { buffer, _ in
            self.processAudio(buffer: buffer)
            do {
                try self.audioFile?.write(from: buffer)
            } catch {
                print("Error writing audio buffer to file: \(error)")
            }
        }
        
        do {
            try engine.start()
            isRecording = true
            print("🎤 Recording started...")
        } catch {
            print("Error starting audio engine: \(error)")
        }
    }
    
    func stopRecording() {
        audioEngine.stop()
        inputNode?.removeTap(onBus: 0)
        isRecording = false
        print("🛑 Recording stopped.")
        
        if let fileURL = fileURL {
            print("Audio file saved at: \(fileURL.path)")
        }
        finalizeSamples()
    }
    
    private func processAudio(buffer: AVAudioPCMBuffer) {
        guard let channelData = buffer.floatChannelData?[0] else { return }
        let channelDataArray = Array(UnsafeBufferPointer(start: channelData,
                                                         count: Int(buffer.frameLength)))
        let level = channelDataArray.map { abs($0) }.reduce(0, +) / Float(channelDataArray.count)
        
        DispatchQueue.main.async {
            self.audioLevel = level
        }
        
        // Log samples for debugging.
        let sampleValues = channelDataArray.map { String(format: "%.5f", $0) }
        print("[\(sampleValues.joined(separator: ", "))]")
        
        sendSamplesToServer(samples: channelDataArray)
    }
    
    private func finalizeSamples() {
        guard let url = URL(string: finalizeString) else {
            print("Invalid finalize URL.")
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
    
        let task = URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                print("Error finalizing samples: \(error)")
            } else if let httpResponse = response as? HTTPURLResponse,
                      httpResponse.statusCode != 200 {
                print("Server returned status code: \(httpResponse.statusCode)")
            } else {
                // If this is the Jarvis endpoint, we expect a JSON response.
                if let data = data,
                   let json = try? JSONSerialization.jsonObject(with: data, options: []) as? [String: Any],
                   let answer = json["answer"] as? String,
                   let agent = json["agent"] as? String {
                    print("Jarvis finalize response: \(json)")
                    print("Agent: \(agent) | Answer: \(answer)")
                    DispatchQueue.main.async {
                        self.onFinalize?(agent, answer)
                    }
                } else {
                    print("Successfully finalized audio samples.")
                }
            }
        }
        task.resume()
    }
    
    private func sendSamplesToServer(samples: [Float]) {
        guard let url = URL(string: uploadURLString) else {
            print("Invalid upload URL.")
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let jsonPayload: [String: Any] = ["samples": samples]
        
        do {
            let data = try JSONSerialization.data(withJSONObject: jsonPayload, options: [])
            request.httpBody = data
        } catch {
            print("Error converting samples to JSON: \(error)")
            return
        }
        
        let task = URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                print("Error uploading samples: \(error)")
            } else if let httpResponse = response as? HTTPURLResponse,
                      httpResponse.statusCode != 200 {
                print("Server returned status code: \(httpResponse.statusCode)")
            } else {
                print("Successfully uploaded \(samples.count) samples.")
            }
        }
        task.resume()
    }
}

// MARK: - ConversationPage (with two audio processors)
struct ConversationPage: View {
    // Regular audio processor (for the mic button)
    @StateObject private var audioProcessor = AudioProcessor()
    // Jarvis audio processor with custom endpoints for Jarvis audio
    @StateObject private var jarvisAudioProcessor = AudioProcessor(
        uploadEndpoint: "https://normal-guiding-orca.ngrok-free.app/upload_samples_jarvis",
        finalizeEndpoint: "https://normal-guiding-orca.ngrok-free.app/finalize_jarvis"
    )
    
    @State private var profile: Profile? = nil
    @StateObject private var contactManager = ContactManager()
    
    // State to hold the Jarvis response text.
    @State private var jarvisResponse: String = ""
    
    var body: some View {
        GeometryReader { geometry in
            ZStack {
                // Left-side Profile View
                HStack {
                    VStack(alignment: .leading) {
                        if let profile = profile {
                            ProfileDescriptionView(
                                name: profile.name,
                                about: profile.about,
                                education: profile.educationText,
                                experiences: profile.experiences,
                                profileURL: profile.profile_url
                            )
                        } else {
                            Text("")
                                .foregroundColor(.black)
                                .font(.system(size: 24, weight: .medium))
                                .padding()
                        }
                        Spacer()
                    }
                    Spacer()
                }
                
                Spacer()
                
                VStack {
                    // Hey JARVIS button uses jarvisAudioProcessor.
                    Button(action: {
                        if jarvisAudioProcessor.isRecording {
                            jarvisAudioProcessor.stopRecording()
                        } else {
                            jarvisAudioProcessor.startRecording()
                        }
                    }) {
                        Text("Hey JARVIS")
                            .font(.system(size: 24, weight: .medium))
                            .foregroundColor(.white)
                            .padding()
                            .frame(maxWidth: 200, maxHeight: 100)
                    }
                    .background(
                        MeshGradient(
                            width: 3,
                            height: 3,
                            points: [
                                .init(0, 0),   .init(0.5, 0),   .init(1, 0),
                                .init(0, 0.5), .init(0.5, 0.5), .init(1, 0.5),
                                .init(0, 1),   .init(0.5, 1),   .init(1, 1)
                            ],
                            colors: [
                                .red,    .purple, .indigo,
                                .orange, .white,  .blue,
                                .yellow, .green,  .mint
                            ]
                        )
                    )
                    .clipShape(RoundedRectangle(cornerRadius: 50, style: .continuous))
                    .padding(.horizontal)
                    
                    HStack {
                        Spacer()
                        // Camera button.
                        Button(action: {
                            print("Taking a picture of the person")
                            Task {
                                do {
                                    try await contactManager.fetchContacts(isFirstCapture: false)
                                    let profileData = try await withCheckedThrowingContinuation { continuation in
                                        NetworkManager.captureGesture { result in
                                            continuation.resume(with: result)
                                        }
                                    }
                                    await MainActor.run {
                                        self.profile = profileData
                                    }
                                } catch {
                                    print("Error in capture process: \(error)")
                                }
                            }
                        }) {
                            Image(systemName: "camera")
                                .resizable()
                                .scaledToFit()
                                .frame(width: 80, height: 80)
                                .foregroundColor(.black)
                                .padding()
                                .background(Color(hex:"e2e2e2"))
                                .clipShape(Circle())
                        }
                        .padding(.trailing, 20)
                        
                        // Mic button uses regular audioProcessor.
                        Button(action: {
                            if audioProcessor.isRecording {
                                audioProcessor.stopRecording()
                            } else {
                                audioProcessor.startRecording()
                            }
                        }) {
                            Image(systemName: audioProcessor.isRecording ? "mic.fill" : "mic")
                                .resizable()
                                .scaledToFit()
                                .frame(width: 80, height: 80)
                                .foregroundColor(.black)
                                .padding()
                                .font(.subheadline)
                                .background(audioProcessor.isRecording ? Color.red : Color(hex: "e2e2e2"))
                                .clipShape(Circle())
                        }
                        .padding(.trailing, 20)
                        Spacer()
                    }
                    
                    // Display Jarvis's response (if any)
                    if !jarvisResponse.isEmpty {
                        Text(jarvisResponse)
                            .font(.system(size: 24, weight: .semibold))
                            .foregroundColor(.black)
                            .padding()
                            .background(Color.gray.opacity(0.5))
                            .cornerRadius(10)
                            .padding(.top, 20)
                    }
                }
            }
        }
        .onAppear {
            audioProcessor.setupAudioSession()
            jarvisAudioProcessor.setupAudioSession()
            
            // Set the onFinalize callback for Jarvis processor.
            jarvisAudioProcessor.onFinalize = { agent, answer in
                jarvisResponse = "Jarvis's \(agent) responds: \(answer)"
            }
            
            Task {
                do {
                    let store = CNContactStore()
                    let granted = try await store.requestAccess(for: .contacts)
                    if granted {
                        try await contactManager.fetchContacts(isFirstCapture: true)
                    } else {
                        print("Contacts permission denied.")
                    }
                } catch {
                    print("Contacts permission error: \(error.localizedDescription)")
                }
            }
        }
    }
}

// MARK: - ProfileDescriptionView
struct ProfileDescriptionView: View {
    let name: String
    let about: String
    let education: String
    let experiences: [[String]]
    let profileURL: String

    var body: some View {
        GeometryReader { geometry in
            VStack(alignment: .leading, spacing: 8) {
                // Name
                Text(name)
                    .foregroundColor(.black)
                    .font(.custom("BricolageGrotesque-96ptExtraBold_Bold", size: 45))
                    .padding(.bottom, 5)
                
                // About
                Text(about)
                    .foregroundColor(.black)
                    .font(.custom("BricolageGrotesque-96ptExtraBold_Light", size: 20))
                    .padding(.leading, 13)
                
                // Education Section
                Text("Education")
                    .foregroundColor(.black)
                    .font(.custom("BricolageGrotesque-96ptExtraBold_SemiBold", size: 30))
                
                Text(education)
                    .foregroundColor(.black)
                    .font(.custom("BricolageGrotesque-96ptExtraBold_Light", size: 30))
                    .padding(.leading, 20)
                
                // Experiences Section
                Text("Experiences")
                    .foregroundColor(.black)
                    .font(.system(size: 30, weight: .semibold, design: .default))
                
                ForEach(experiences, id: \.self) { experience in
                    if experience.count == 2 {
                        HStack {
                            Text(experience[0])
                            Text("•")
                            Text(experience[1])
                        }
                        .foregroundColor(.black)
                        .font(.custom("BricolageGrotesque-96ptExtraBold_Light", size: 30))
                    } else if experience.count == 3 {
                        DisclosureGroup {
                            Text(experience[2])
                                .foregroundColor(.black)
                                .font(.custom("BricolageGrotesque-96ptExtraBold_Light", size: 20))
                                .padding(.leading, 13)
                        } label: {
                            HStack {
                                Text(experience[0])
                                Text("•")
                                Text(experience[1])
                            }
                            .foregroundColor(.black)
                            .font(.custom("BricolageGrotesque-96ptExtraBold_Light", size: 30))
                        }
                    } else {
                        Text(experience.joined(separator: " • "))
                            .foregroundColor(.black)
                            .font(.custom("BricolageGrotesque-96ptExtraBold_Light", size: 30))
                    }
                }
                
                // Profile URL
                Text("Profile URL: \(profileURL)")
                    .foregroundColor(.blue)
                    .underline()
            }
            .frame(width: 800)
            .padding(40)
            .background(
                RoundedRectangle(cornerRadius: 30)
                    .fill(Color(hex: "E2E2E2").opacity(0.6))
            )
        }
    }
}

// MARK: - Preview
struct ConversationPage_Preview: PreviewProvider {
    static var previews: some View {
        ConversationPage()
    }
}

// MARK: - Extensions
extension Color {
    init(hex: String) {
        let sanitizedHex = hex
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .replacingOccurrences(of: "#", with: "")
        var rgbValue: UInt64 = 0
        Scanner(string: sanitizedHex).scanHexInt64(&rgbValue)

        let r, g, b, a: UInt64
        switch sanitizedHex.count {
        case 6:
            r = (rgbValue >> 16) & 0xFF
            g = (rgbValue >> 8) & 0xFF
            b = rgbValue & 0xFF
            a = 0xFF
        case 8:
            r = (rgbValue >> 24) & 0xFF
            g = (rgbValue >> 16) & 0xFF
            b = (rgbValue >> 8) & 0xFF
            a = rgbValue & 0xFF
        default:
            r = 255; g = 255; b = 255; a = 255
        }
        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue: Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}

extension CNContact {
    var normalizedPhoneNumbers: [String] {
        return phoneNumbers.map { phone in
            let rawNumber = phone.value.stringValue
            let digits = rawNumber.filter { $0.isWholeNumber }
            
            if digits.count == 11 && digits.first == "1" {
                return String(digits.dropFirst())
            }
            
            if digits.count > 10 {
                return String(digits.suffix(10))
            }
            
            return digits
        }
    }
    
    var lowercasedEmails: [String] {
        return emailAddresses.map { ($0.value as String).lowercased() }
    }
}
