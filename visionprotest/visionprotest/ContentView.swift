//
//  ContentView.swift
//  visionprotest
//
//  Created by Kaival Shah on 2/14/25.
//

import SwiftUI
import RealityKit
import RealityKitContent
import AVFoundation

struct ContentView: View {
    var body: some View {
        VStack {
            Model3D(named: "Scene", bundle: realityKitContentBundle)
                .padding(.bottom, 50)

            Text("Vision pro test")
        }
        .padding()
    }
}

#Preview(windowStyle: .automatic) {
    ContentView()
}
