$ErrorActionPreference = "Stop"

$jdkDir = "C:\Users\jessi\AppData\Local\Android\jdk17\jdk-17.0.20.1+1"
$buildTools = "C:\Users\jessi\AppData\Local\Android\Sdk\build-tools\34.0.0"
$platformJar = "C:\Users\jessi\AppData\Local\Android\Sdk\platforms\android-36\android.jar"

$javac = "$jdkDir\bin\javac.exe"
$keytool = "$jdkDir\bin\keytool.exe"
$aapt = "$buildTools\aapt.exe"
$d8 = "$buildTools\d8.bat"
$zipalign = "$buildTools\zipalign.exe"
$apksigner = "$buildTools\apksigner.bat"

$workDir = "c:\Users\jessi\Documents\New folder\apk_build"
if (Test-Path $workDir) { Remove-Item $workDir -Recurse -Force }
New-Item -ItemType Directory -Path "$workDir\src\com\example\onionlens" -Force | Out-Null
New-Item -ItemType Directory -Path "$workDir\bin" -Force | Out-Null
New-Item -ItemType Directory -Path "$workDir\res\drawable" -Force | Out-Null
New-Item -ItemType Directory -Path "$workDir\res\values" -Force | Out-Null
New-Item -ItemType Directory -Path "$workDir\assets\static" -Force | Out-Null

# Copy static web app to assets
Copy-Item -Path "c:\Users\jessi\Documents\New folder\static\*" -Destination "$workDir\assets\static" -Recurse -Force
# Copy logo to drawable
Copy-Item -Path "c:\Users\jessi\Documents\New folder\static\images\logo.png" -Destination "$workDir\res\drawable\ic_launcher.png" -Force

# Create strings.xml
@"
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">Onion Lens</string>
</resources>
"@ | Set-Content "$workDir\res\values\strings.xml" -Encoding UTF8

# Create AndroidManifest.xml
@"
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.example.onionlens"
    android:versionCode="1"
    android:versionName="1.0.0">

    <uses-sdk android:minSdkVersion="24" android:targetSdkVersion="34" />

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.CAMERA" />
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />

    <uses-feature android:name="android.hardware.camera" android:required="false" />
    <uses-feature android:name="android.hardware.camera.autofocus" android:required="false" />

    <application
        android:label="Onion Lens"
        android:icon="@drawable/ic_launcher"
        android:usesCleartextTraffic="true">
        <activity
            android:name="com.example.onionlens.MainActivity"
            android:exported="true"
            android:configChanges="orientation|screenSize|keyboardHidden"
            android:theme="@android:style/Theme.NoTitleBar">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
"@ | Set-Content "$workDir\AndroidManifest.xml" -Encoding UTF8

$sourceCode = 
@"
package com.example.onionlens;

import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.view.KeyEvent;
import android.view.View;
import android.view.ViewGroup;
import android.view.Window;
import android.view.WindowManager;
import android.webkit.PermissionRequest;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;

public class MainActivity extends Activity {

    private WebView webView;
    private ValueCallback<Uri[]> fileUploadCallback;
    private static final int FILE_CHOOSER_REQ_CODE = 1001;
    private static final int PERMISSION_REQ_CODE = 1002;

    private static final String REMOTE_URL = "http://10.175.205.78:8000";
    private static final String LOCAL_ASSET_URL = "file:///android_asset/static/index.html";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        requestWindowFeature(Window.FEATURE_NO_TITLE);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            Window window = getWindow();
            window.addFlags(WindowManager.LayoutParams.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS);
            window.setStatusBarColor(Color.parseColor("#872B43"));
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            String[] perms = new String[] {
                "android.permission.CAMERA",
                "android.permission.READ_EXTERNAL_STORAGE"
            };
            requestPermissions(perms, PERMISSION_REQ_CODE);
        }

        FrameLayout rootLayout = new FrameLayout(this);
        rootLayout.setLayoutParams(new ViewGroup.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,
            ViewGroup.LayoutParams.MATCH_PARENT
        ));
        rootLayout.setBackgroundColor(Color.parseColor("#872B43"));

        webView = new WebView(this);
        webView.setLayoutParams(new FrameLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,
            ViewGroup.LayoutParams.MATCH_PARENT
        ));
        webView.setScrollBarStyle(View.SCROLLBARS_INSIDE_OVERLAY);

        setupWebView();
        rootLayout.addView(webView);
        setContentView(rootLayout);

        webView.loadUrl(REMOTE_URL);
    }

    private void setupWebView() {
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        settings.setAllowFileAccessFromFileURLs(true);
        settings.setAllowUniversalAccessFromFileURLs(true);
        settings.setMediaPlaybackRequiresUserGesture(false);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            settings.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        }
        settings.setLoadWithOverviewMode(true);
        settings.setUseWideViewPort(true);

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                super.onReceivedError(view, request, error);
                if (request != null && request.isForMainFrame() && !view.getUrl().startsWith("file://")) {
                    view.loadUrl(LOCAL_ASSET_URL);
                }
            }
        });

        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onPermissionRequest(final PermissionRequest request) {
                if (request != null) {
                    request.grant(request.getResources());
                }
            }

            @Override
            public boolean onShowFileChooser(WebView webView, ValueCallback<Uri[]> filePathCallback, FileChooserParams fileChooserParams) {
                fileUploadCallback = filePathCallback;
                Intent intent = new Intent(Intent.ACTION_GET_CONTENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType("image/*");
                Intent chooser = Intent.createChooser(intent, "Select Onion Photo");
                startActivityForResult(chooser, FILE_CHOOSER_REQ_CODE);
                return true;
            }
        });
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        if (requestCode == FILE_CHOOSER_REQ_CODE) {
            if (fileUploadCallback != null) {
                Uri[] results = null;
                if (resultCode == RESULT_OK && data != null && data.getData() != null) {
                    results = new Uri[] { data.getData() };
                }
                fileUploadCallback.onReceiveValue(results);
                fileUploadCallback = null;
            }
            return;
        }
        super.onActivityResult(requestCode, resultCode, data);
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_BACK && webView.canGoBack()) {
            webView.goBack();
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }
}
"@ | Set-Content "$workDir\src\com\example\onionlens\MainActivity.java" -Encoding ASCII

Write-Host "1. Compiling Android Resources with aapt..."
& $aapt package -f -m -J "$workDir\src" -M "$workDir\AndroidManifest.xml" -S "$workDir\res" -I $platformJar

Write-Host "2. Compiling Java Sources..."
$javaFiles = Get-ChildItem "$workDir\src" -Recurse -Filter "*.java" | ForEach-Object { $_.FullName }
& $javac -source 17 -target 17 -cp $platformJar -d "$workDir\bin" $javaFiles

Write-Host "3. Generating classes.dex with d8..."
$classFiles = Get-ChildItem "$workDir\bin" -Recurse -Filter "*.class" | ForEach-Object { "`"$($_.FullName)`"" }
$classArgs = $classFiles -join ' '
$env:JAVA_HOME = $jdkDir
$env:PATH = "$jdkDir\bin;$env:PATH"
cmd.exe /c "`"$d8`" --output `"$workDir`" --lib `"$platformJar`" $classArgs"

Write-Host "4. Packaging APK with aapt..."
& $aapt package -f -M "$workDir\AndroidManifest.xml" -S "$workDir\res" -A "$workDir\assets" -I $platformJar -F "$workDir\onion-lens-unaligned.apk"
Set-Location $workDir
& $aapt add "$workDir\onion-lens-unaligned.apk" classes.dex
Set-Location "c:\Users\jessi\Documents\New folder"

Write-Host "5. Zipaligning APK..."
& $zipalign -f -p 4 "$workDir\onion-lens-unaligned.apk" "$workDir\onion-lens-aligned.apk"

Write-Host "6. Generating Debug Keystore if needed..."
$keystore = "$workDir\debug.keystore"
if (-not (Test-Path $keystore)) {
    & $keytool -genkey -v -keystore $keystore -storepass android -alias androiddebugkey -keypass android -keyalg RSA -keysize 2048 -validity 10000 -dname "CN=Android Debug,O=Android,C=US"
}

Write-Host "7. Signing APK with apksigner..."
$finalApk = "c:\Users\jessi\Documents\New folder\onion-lens.apk"
$staticApk = "c:\Users\jessi\Documents\New folder\static\onion-lens.apk"
cmd.exe /c "$apksigner sign --ks `"$keystore`" --ks-pass pass:android --out `"$finalApk`" `"$workDir\onion-lens-aligned.apk`""
Copy-Item $finalApk $staticApk -Force

Write-Host "SUCCESS! APK Generated at:"
Write-Host "  $finalApk ($((Get-Item $finalApk).Length) bytes)"
Write-Host "  $staticApk ($((Get-Item $staticApk).Length) bytes)"

