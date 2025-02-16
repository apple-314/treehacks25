////
////  ContentView.swift
////  SuperVision
////
////  Created by Aarav Wattal on 2/15/25.
////
//
//import SwiftUI
//import RealityKit
//import RealityKitContent
//import Contacts
//
//struct ContentView: View {
//    @State private var contactAccessMessage: String = ""
//
//    var body: some View {
//        VStack {
//            Model3D(named: "Scene", bundle: realityKitContentBundle)
//                .padding(.bottom, 50)
//            
//            Text("Hello, world!")
//            
//            Button("Request Contacts Access") {
//                requestContactsAccess()
//            }
//            .padding()
//            
//            if !contactAccessMessage.isEmpty {
//                Text(contactAccessMessage)
//                    .padding()
//            }
//        }
//        .padding()
//    }
//    
//    private func requestContactsAccess() {
//        let store = CNContactStore()
//        store.requestAccess(for: .contacts) { granted, error in
//            DispatchQueue.main.async {
//                if granted {
//                    contactAccessMessage = "Contacts access granted."
//                } else {
//                    let errorMessage = error?.localizedDescription ?? "Access denied."
//                    contactAccessMessage = "Contacts access denied: \(errorMessage)"
//                }
//            }
//        }
//    }
//}
//
//#Preview(windowStyle: .automatic) {
//    ContentView()
//}
