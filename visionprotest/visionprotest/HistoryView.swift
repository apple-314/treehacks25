import SwiftUI

struct LinkedInProfile: Codable {
    let bio: String
    let experiences: [String]
    let education: [String]
}

struct APIProfile: Codable {
    let LinkedIn: LinkedInProfile
    let convos: [String]
    let interests: String?
    let img: String
}

struct PersonProfile: Identifiable {
    let id = UUID()
    let name: String
    let interests: String
    let bio: String
    let experiences: [String]
    let education: [String]
    let img: String
}

class ProfilesViewModel: ObservableObject {
    @Published var profiles: [PersonProfile] = []
    @Published var errorMessage: String? = nil
    
    func fetchProfiles() {
        guard let url = URL(string: "http://127.0.0.1:8000/get_profiles") else {
            self.errorMessage = "Invalid URL"
            return
        }
        
        URLSession.shared.dataTask(with: url) { data, response, error in
            if let error = error {
                DispatchQueue.main.async {
                    self.errorMessage = "Error: \(error.localizedDescription)"
                }
                return
            }
            guard let data = data else {
                DispatchQueue.main.async {
                    self.errorMessage = "No data received"
                }
                return
            }
            do {
                if let rawJSON = String(data: data, encoding: .utf8) {
                    print("Raw JSON on success: \(rawJSON)")
                }
                
                let decoded = try JSONDecoder().decode([String: APIProfile].self, from: data)
                print("Decoded dictionary: \(decoded)")
                
                let profiles = decoded.map { (name, apiProfile) in
                    PersonProfile(
                        name: name,
                        interests: apiProfile.interests ?? "No interests listed",
                        bio: apiProfile.LinkedIn.bio,
                        experiences: apiProfile.LinkedIn.experiences,
                        education: apiProfile.LinkedIn.education,
                        img: apiProfile.img
                    )
                }
                
                DispatchQueue.main.async {
                    self.profiles = profiles
                }
            } catch {
                print("Decoding error: \(error)")
                DispatchQueue.main.async {
                    self.errorMessage = "Error decoding data: \(error.localizedDescription)"
                }
            }
        }.resume()
    }
}

struct HistoryView: View {
    @StateObject private var viewModel = ProfilesViewModel()
    
    var body: some View {
        GeometryReader { geometry in
            ScrollView {
                LazyVGrid(columns: [
                    GridItem(.flexible(), spacing: 16),
                    GridItem(.flexible(), spacing: 16)
                ], spacing: 16) {
                    ForEach(viewModel.profiles) { profile in
                        VStack(alignment: .leading, spacing: 8) {
                            AsyncImage(url: URL(string: profile.img)) { image in
                                image
                                    .resizable()
                                    .aspectRatio(contentMode: .fill)
                            } placeholder: {
                                Color.gray
                            }
                            .frame(height: 200)
                            .clipped()
                            
                            Text(profile.name)
                                .font(.headline)
                            
                            Text(profile.bio)
                                .font(.subheadline)
                                .lineLimit(3)
                            
                            Text("Interests:")
                                .font(.subheadline)
                                .bold()
                            Text(profile.interests)
                                .font(.caption)
                                .lineLimit(2)
                            
                            if !profile.education.isEmpty {
                                Text("Education:")
                                    .font(.subheadline)
                                    .bold()
                                ForEach(profile.education.prefix(2), id: \.self) { edu in
                                    Text(edu)
                                        .font(.caption)
                                }
                            }
                            
                            if !profile.experiences.isEmpty {
                                Text("Experience:")
                                    .font(.subheadline)
                                    .bold()
                                ForEach(profile.experiences.prefix(2), id: \.self) { exp in
                                    Text(exp)
                                        .font(.caption)
                                }
                            }
                        }
                        .padding()
                        .background(Color(.systemBackground))
                        .cornerRadius(10)
                        .shadow(radius: 5)
                    }
                }
                .padding()
            }
        }
        .navigationTitle("History")
        .onAppear {
            viewModel.fetchProfiles()
        }
    }
}

struct HistoryView_Previews: PreviewProvider {
    static var previews: some View {
        NavigationView {
            HistoryView()
        }
    }
}
