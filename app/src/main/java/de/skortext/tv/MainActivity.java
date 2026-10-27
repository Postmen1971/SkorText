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
	private static final String APP_URL = "file:///android_asset/www/index.html";
	private boolean appLoaded = false;
	private final Handler ui = new Handler(Looper.getMainLooper());
	private int repairs = 0;
	private long lastRepair = 0;

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		getWindow().addFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN);
		prefs = getSharedPreferences("skortext", MODE_PRIVATE);
		createWeb();
		watchdog(5000);
	}

	/** Oberflaeche (neu) aufbauen - auch, wenn Android den Anzeige-Prozess im Hintergrund beendet hat. */
	private void createWeb() {
		if (web != null) {
			try { ((android.view.ViewGroup) web.getParent()).removeView(web); } catch (Exception e) {}
			try { web.destroy(); } catch (Exception e) {}
		}
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
			public boolean onRenderProcessGone(WebView view, android.webkit.RenderProcessGoneDetail detail) {
				// Anzeige-Prozess wurde beendet -> sonst bleibt der Bildschirm schwarz
				ui.post(new Runnable() { @Override public void run() { createWeb(); watchdog(5000); } });
				return true;
			}
		});
		setContentView(web);
		appLoaded = true;
		web.loadUrl(APP_URL);
		web.requestFocus(View.FOCUS_DOWN);
	}

	/** Prueft nach kurzer Zeit, ob die Seite lebt und zeichnet; wenn nicht, wird sie neu geladen. */
	private void watchdog(long delay) {
		ui.postDelayed(new Runnable() {
			@Override
			public void run() {
				if (web == null || isFinishing()) return;
				final boolean[] alive = {false};
				web.evaluateJavascript("window.skorAlive ? window.skorAlive() : 'no'", new ValueCallback<String>() {
					@Override
					public void onReceiveValue(String v) { alive[0] = "\"ok\"".equals(v); }
				});
				ui.postDelayed(new Runnable() {
					@Override
					public void run() {
						if (alive[0] || web == null || isFinishing()) return;
						long now = System.currentTimeMillis();
						if (now - lastRepair > 60000) repairs = 0;
						if (repairs >= 3) return;
						repairs++;
						lastRepair = now;
						if (repairs == 1) web.reload(); else createWeb();
						watchdog(5000);
					}
				}, 2500);
			}
		}, delay);
	}

	@Override
	protected void onResume() {
		super.onResume();
		if (web != null) {
			web.onResume();
			web.resumeTimers();
			web.requestFocus(View.FOCUS_DOWN);
			watchdog(1200);
		}
	}

	@Override
	protected void onPause() {
		if (web != null) web.onPause();
		super.onPause();
	}

	@Override
	public void onWindowFocusChanged(boolean hasFocus) {
		super.onWindowFocusChanged(hasFocus);
		if (hasFocus && web != null) web.evaluateJavascript("window.skorAlive && window.skorAlive()", null);
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
		ui.removeCallbacksAndMessages(null);
		if (web != null) web.destroy();
		super.onDestroy();
	}

	private void status(final String st) {
		runOnUiThread(new Runnable() {
			@Override
			public void run() {
				if (web != null) web.evaluateJavascript("window.__skorUpd && window.__skorUpd(" + JSONObject.quote(st) + ")", null);
			}
		});
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
							// Zeichensatz aus der Antwort (TFF-Seiten sind windows-1254 = Türkisch)
							String cs = url.contains("tff.org") ? "windows-1254" : "UTF-8";
							String ct = c.getContentType();
							if (ct != null && ct.toLowerCase().contains("charset=")) cs = ct.substring(ct.toLowerCase().indexOf("charset=") + 8).replace("\"", "").split(";")[0].trim();
							try { body = out.toString(cs); } catch (Exception ce) { body = out.toString("UTF-8"); }
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

		/** Update: APK laden und das Android-Installationsfenster öffnen. */
		@JavascriptInterface
		public void installApk(final String url) {
			new Thread(new Runnable() {
				@Override
				public void run() {
					HttpURLConnection c = null;
					try {
						c = (HttpURLConnection) new URL(url).openConnection();
						c.setInstanceFollowRedirects(true);
						c.setConnectTimeout(15000);
						c.setReadTimeout(60000);
						int code = c.getResponseCode();
						// GitHub leitet auf einen anderen Server weiter
						for (int i = 0; i < 5 && (code == 301 || code == 302 || code == 303 || code == 307 || code == 308); i++) {
							String loc = c.getHeaderField("Location");
							c.disconnect();
							c = (HttpURLConnection) new URL(new URL(url), loc).openConnection();
							c.setConnectTimeout(15000);
							c.setReadTimeout(60000);
							code = c.getResponseCode();
						}
						if (code != 200) throw new IOException("HTTP " + code);
						java.io.File f = ApkProvider.file(MainActivity.this);
						InputStream in = c.getInputStream();
						java.io.FileOutputStream out = new java.io.FileOutputStream(f);
						byte[] buf = new byte[65536];
						int n;
						while ((n = in.read(buf)) > 0) out.write(buf, 0, n);
						out.close();
						in.close();
						runOnUiThread(new Runnable() {
							@Override
							public void run() {
								try {
									if (android.os.Build.VERSION.SDK_INT >= 26 && !getPackageManager().canRequestPackageInstalls()) {
										// einmalig erlauben: "Unbekannte Apps installieren" für SkorText
										startActivity(new android.content.Intent(android.provider.Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,
											Uri.parse("package:" + getPackageName())));
										status("perm");
										return;
									}
									android.content.Intent it = new android.content.Intent(android.content.Intent.ACTION_VIEW);
									it.setDataAndType(Uri.parse("content://" + ApkProvider.AUTH + "/skortext.apk"), "application/vnd.android.package-archive");
									it.addFlags(android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION | android.content.Intent.FLAG_ACTIVITY_NEW_TASK);
									startActivity(it);
									status("open");
								} catch (Exception e) {
									status("error:" + e.getMessage());
								}
							}
						});
					} catch (Exception e) {
						status("error:" + e.getMessage());
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
