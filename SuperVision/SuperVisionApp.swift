//
//  SuperVisionApp.swift
//  SuperVision
//
//  Created by Aarav Wattal on 2/15/25.
//

import SwiftUI

@main
struct SuperVisionApp: App {
    var body: some Scene {
        WindowGroup {
//            ContentView()
            AudioProcessing()
                .padding()
                .background(.clear)
                .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
    }
}
