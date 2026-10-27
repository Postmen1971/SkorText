package de.skortext.tv;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.provider.OpenableColumns;

import java.io.File;
import java.io.FileNotFoundException;

/** Gibt die heruntergeladene Update-APK an das Android-Installationsfenster weiter. */
public class ApkProvider extends ContentProvider {
	public static final String AUTH = "de.skortext.tv.apk";

	static File file(android.content.Context c) {
		return new File(c.getCacheDir(), "skortext-update.apk");
	}

	@Override public boolean onCreate() { return true; }

	@Override
	public ParcelFileDescriptor openFile(Uri uri, String mode) throws FileNotFoundException {
		return ParcelFileDescriptor.open(file(getContext()), ParcelFileDescriptor.MODE_READ_ONLY);
	}

	@Override public String getType(Uri uri) { return "application/vnd.android.package-archive"; }

	@Override
	public Cursor query(Uri uri, String[] p, String s, String[] a, String o) {
		File f = file(getContext());
		MatrixCursor c = new MatrixCursor(new String[] {OpenableColumns.DISPLAY_NAME, OpenableColumns.SIZE});
		c.addRow(new Object[] {"skortext.apk", f.length()});
		return c;
	}

	@Override public Uri insert(Uri uri, ContentValues v) { return null; }
	@Override public int delete(Uri uri, String s, String[] a) { return 0; }
	@Override public int update(Uri uri, ContentValues v, String s, String[] a) { return 0; }
}
