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

struct HistoryPage: View {
    @StateObject private var viewModel = ProfilesViewModel()
    
    var body: some View {
        GeometryReader { geometry in
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 20) {
                    ForEach(viewModel.profiles) { profile in
                        VStack(alignment: .center, spacing: 8) {
                            AsyncImage(url: URL(string: profile.img)) { image in
                                image
                                    .resizable()
                                    .aspectRatio(contentMode: .fill)
                            } placeholder: {
                                Color.gray
                            }
                            .frame(width: 100, height: 100)
                            .clipShape(Circle())
                            
                            Text(profile.name)
                                .font(.headline)
                                .lineLimit(1)
                            
                            Text(profile.interests)
                                .font(.subheadline)
                                .lineLimit(1)
                                .foregroundColor(.white)
                        }
                        .frame(width: .infinity)
                        .frame(height: geometry.size.height * 0.8)
                        .padding(.vertical)
                    }
                }
                .frame(minHeight: geometry.size.height)
                .padding(.horizontal, 40)
            }
        }
        .navigationTitle("History")
        .onAppear {
            viewModel.fetchProfiles()
        }
    }
}

struct HistoryPage_Previews: PreviewProvider {
    static var previews: some View {
        NavigationView {
            HistoryPage()
        }
    }
}
