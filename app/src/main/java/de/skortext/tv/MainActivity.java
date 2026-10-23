package de.skortext.tv;

import android.app.Activity;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.os.Bundle;
import android.view.KeyEvent;
import android.view.View;
import android.view.WindowManager;
import android.net.Uri;
import android.os.Handler;
import android.os.Looper;
import android.webkit.CookieManager;
import android.webkit.JavascriptInterface;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.ValueCallback;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import org.json.JSONObject;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.zip.GZIPInputStream;

/**
 * SkorText fuer Android TV / NVIDIA Shield.
 * Die Oberflaeche ist eine lokale Webseite (assets/www). Diese Huelle leitet die
 * Fernbedienung weiter und holt die Daten (ohne Browser-Sperren fuer fremde Seiten).
 */
public class MainActivity extends Activity {
	private WebView web;
	private SharedPreferences prefs;
	// Die App-Seite wird unter der Sofascore-Adresse ausgeliefert (aus den eingebauten Dateien).
	// So holt der eingebaute Chrome die Daten selbst - wie bei einem normalen Webseitenbesuch.
	private static final String HOST = "www.sofascore.com";
	private static final String APP_URL = "https://" + HOST + "/skortext/index.html";
	private static final String WARM_URL = "https://" + HOST + "/";
	private boolean appLoaded = false;

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		getWindow().addFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN);
		prefs = getSharedPreferences("skortext", MODE_PRIVATE);
		web = new WebView(this);
		web.setBackgroundColor(Color.BLACK);
		web.setFocusable(true);
		web.setFocusableInTouchMode(true);
		WebSettings s = web.getSettings();
		s.setJavaScriptEnabled(true);
		s.setDomStorageEnabled(true);
		s.setAllowFileAccess(true);
		s.setTextZoom(100);
		web.addJavascriptInterface(new Bridge(), "SkorBridge");
		CookieManager cm = CookieManager.getInstance();
		cm.setAcceptCookie(true);
		if (android.os.Build.VERSION.SDK_INT >= 21) cm.setAcceptThirdPartyCookies(web, true);
		web.setWebViewClient(new WebViewClient() {
			@Override
			public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest req) {
				Uri u = req.getUrl();
				String path = u.getPath();
				if (HOST.equals(u.getHost()) && path != null && path.startsWith("/skortext/")) {
					String asset = "www/" + path.substring("/skortext/".length());
					try {
						return new WebResourceResponse(mime(asset), "utf-8", getAssets().open(asset));
					} catch (IOException e) {
						return new WebResourceResponse("text/plain", "utf-8", 404, "Not Found", null, new ByteArrayInputStream(new byte[0]));
					}
				}
				return null;
			}

			@Override
			public void onPageFinished(WebView view, String url) {
				// Erst ein normaler Seitenbesuch bei Sofascore (Cookies/Pruefung), dann die App laden
				if (!appLoaded && url != null && url.startsWith(WARM_URL) && !url.contains("/skortext/")) {
					appLoaded = true;
					new Handler(Looper.getMainLooper()).postDelayed(new Runnable() {
						@Override
						public void run() { web.loadUrl(APP_URL); }
					}, 2500);
				}
			}
		});
		setContentView(web);
		web.loadUrl(WARM_URL);
		new Handler(Looper.getMainLooper()).postDelayed(new Runnable() {
			@Override
			public void run() {
				if (!appLoaded) { appLoaded = true; web.loadUrl(APP_URL); }
			}
		}, 12000);
		web.requestFocus(View.FOCUS_DOWN);
	}

	private static String mime(String name) {
		if (name.endsWith(".html")) return "text/html";
		if (name.endsWith(".js")) return "application/javascript";
		if (name.endsWith(".css")) return "text/css";
		if (name.endsWith(".ttf")) return "font/ttf";
		if (name.endsWith(".png")) return "image/png";
		return "application/octet-stream";
	}

	private static String mapKey(int code) {
		switch (code) {
			case KeyEvent.KEYCODE_DPAD_UP: return "up";
			case KeyEvent.KEYCODE_DPAD_DOWN: return "down";
			case KeyEvent.KEYCODE_DPAD_LEFT: return "left";
			case KeyEvent.KEYCODE_DPAD_RIGHT: return "right";
			case KeyEvent.KEYCODE_DPAD_CENTER:
			case KeyEvent.KEYCODE_ENTER:
			case KeyEvent.KEYCODE_NUMPAD_ENTER:
			case KeyEvent.KEYCODE_BUTTON_A: return "ok";
			case KeyEvent.KEYCODE_BACK:
			case KeyEvent.KEYCODE_ESCAPE:
			case KeyEvent.KEYCODE_BUTTON_B: return "back";
			case KeyEvent.KEYCODE_PROG_RED: return "red";
			case KeyEvent.KEYCODE_PROG_GREEN: return "green";
			case KeyEvent.KEYCODE_PROG_YELLOW: return "yellow";
			case KeyEvent.KEYCODE_PROG_BLUE: return "blue";
			case KeyEvent.KEYCODE_CHANNEL_UP:
			case KeyEvent.KEYCODE_PAGE_UP:
			case KeyEvent.KEYCODE_MEDIA_NEXT: return "chup";
			case KeyEvent.KEYCODE_CHANNEL_DOWN:
			case KeyEvent.KEYCODE_PAGE_DOWN:
			case KeyEvent.KEYCODE_MEDIA_PREVIOUS: return "chdn";
			case KeyEvent.KEYCODE_MENU:
			case KeyEvent.KEYCODE_BUTTON_Y: return "menu";
			case KeyEvent.KEYCODE_INFO:
			case KeyEvent.KEYCODE_BUTTON_X: return "info";
			default:
				if (code >= KeyEvent.KEYCODE_0 && code <= KeyEvent.KEYCODE_9) return String.valueOf(code - KeyEvent.KEYCODE_0);
				if (code >= KeyEvent.KEYCODE_NUMPAD_0 && code <= KeyEvent.KEYCODE_NUMPAD_9) return String.valueOf(code - KeyEvent.KEYCODE_NUMPAD_0);
				return null;
		}
	}

	@Override
	public boolean dispatchKeyEvent(KeyEvent event) {
		String k = mapKey(event.getKeyCode());
		if (k == null) return super.dispatchKeyEvent(event);
		if (!appLoaded) return true;
		if (event.getAction() == KeyEvent.ACTION_DOWN) {
			web.evaluateJavascript("window.skorKey ? window.skorKey('" + k + "') : ''", new ValueCallback<String>() {
				@Override
				public void onReceiveValue(String value) {
					if ("\"exit\"".equals(value)) finish();
				}
			});
		}
		return true;
	}

	@Override
	protected void onDestroy() {
		if (web != null) web.destroy();
		super.onDestroy();
	}

	private void deliver(final int id, final boolean ok, final int status, final String body) {
		final String js = "window.__skorRes(" + id + "," + ok + "," + status + "," + JSONObject.quote(body == null ? "" : body) + ")";
		runOnUiThread(new Runnable() {
			@Override
			public void run() {
				if (web != null) web.evaluateJavascript(js, null);
			}
		});
	}

	private class Bridge {
		@JavascriptInterface
		public void get(final int id, final String url) {
			new Thread(new Runnable() {
				@Override
				public void run() {
					HttpURLConnection c = null;
					try {
						c = (HttpURLConnection) new URL(url).openConnection();
						c.setConnectTimeout(12000);
						c.setReadTimeout(15000);
						c.setRequestProperty("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36");
						c.setRequestProperty("Accept", "application/json, application/rss+xml, application/xml, text/xml, */*");
						c.setRequestProperty("Accept-Language", "de-DE,de;q=0.9,tr;q=0.8,en;q=0.7");
						c.setRequestProperty("Accept-Encoding", "gzip");
						if (url.contains("sofascore")) {
							c.setRequestProperty("Referer", "https://www.sofascore.com/");
							c.setRequestProperty("Origin", "https://www.sofascore.com");
						}
						int code = c.getResponseCode();
						InputStream in = code >= 400 ? c.getErrorStream() : c.getInputStream();
						String body = "";
						if (in != null) {
							if ("gzip".equalsIgnoreCase(c.getContentEncoding())) in = new GZIPInputStream(in);
							ByteArrayOutputStream out = new ByteArrayOutputStream();
							byte[] buf = new byte[16384];
							int n;
							while ((n = in.read(buf)) > 0) out.write(buf, 0, n);
							in.close();
							body = out.toString("UTF-8");
						}
						deliver(id, true, code, body);
					} catch (Exception e) {
						deliver(id, false, 0, e.getClass().getSimpleName() + ": " + e.getMessage());
					} finally {
						if (c != null) c.disconnect();
					}
				}
			}).start();
		}

		@JavascriptInterface
		public String pref(String key, String def) {
			return prefs.getString(key, def);
		}

		@JavascriptInterface
		public void setPref(String key, String value) {
			prefs.edit().putString(key, value).apply();
		}
	}
}
