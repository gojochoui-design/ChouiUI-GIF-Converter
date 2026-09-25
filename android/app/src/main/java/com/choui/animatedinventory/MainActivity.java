package com.choui.animatedinventory;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.database.Cursor;
import android.provider.DocumentsContract;
import android.provider.OpenableColumns;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Color;
import android.graphics.Movie;
import android.graphics.PorterDuff;
import android.graphics.Rect;
import android.graphics.drawable.Drawable;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.view.View;
import android.widget.ImageView;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.HashMap;
import java.util.Map;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;
import org.json.JSONArray;
import org.json.JSONObject;
public class MainActivity extends Activity {
    static final int MAX_FLIPBOOK_FRAMES = 23;
    static final int MAX_FLIPBOOK_SEGMENTS = 8;

    static final int REQ_PERM = 7;

    File gifFile;
    File pendingOutput;
    Uri outputTree;
    String gifDisplayName = "Animated Inventory";

    ImageView preview;
    TextView info, status, folderValue, placeholderText;
    android.widget.Button selectButton, convertButton, folderButton;
    ProgressBar progress;
    final Handler handler = new Handler(Looper.getMainLooper());
    Movie previewMovie;
    Bitmap firstPreview, inventoryBase, inventoryLines;
    int previewTime=0, previewDuration=100, previewStep=100;
    long previewStartMs;

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        try {
            inventoryBase = BitmapFactory.decodeStream(getAssets().open("template/textures/ui/inventory.png"));
            inventoryLines = BitmapFactory.decodeStream(getAssets().open("template/textures/ui/inventory_lines.png"));
        } catch (Exception ignored) {}

        preview = findViewById(R.id.preview);
        info = findViewById(R.id.info);
        status = findViewById(R.id.status);
        folderValue = findViewById(R.id.folderValue);
        placeholderText = findViewById(R.id.placeholderText);
        selectButton = findViewById(R.id.selectButton);
        convertButton = findViewById(R.id.convertButton);
        folderButton = findViewById(R.id.folderButton);
        progress = findViewById(R.id.progress);

        String saved = getPreferences(0).getString("outputTree", "");
        if (!saved.isEmpty()) {
            outputTree = Uri.parse(saved);
            folderValue.setText("Folder selected");
        }

        selectButton.setOnClickListener(v -> pickGif());
        convertButton.setOnClickListener(v -> convert());
        folderButton.setOnClickListener(v -> changeFolder());

    }


    void pickGif() {
        Intent i = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        i.setType("image/*");
        i.putExtra(Intent.EXTRA_MIME_TYPES, new String[]{"image/gif", "image/*"});
        i.addCategory(Intent.CATEGORY_OPENABLE);
        i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
        startActivityForResult(i, 1);
    }

    void changeFolder() {
        Intent i = new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
        i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
        startActivityForResult(i, 2);
    }

    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (resultCode != RESULT_OK || data == null) return;
        if (requestCode == 1) {
            try {
                Uri u = data.getData();
                try { getContentResolver().takePersistableUriPermission(u, data.getFlags() & Intent.FLAG_GRANT_READ_URI_PERMISSION); } catch (Exception ignored) {}
                gifFile = new File(getCacheDir(), "selected.gif");
                gifDisplayName = displayNameFor(u);
                try (InputStream in = getContentResolver().openInputStream(u); OutputStream out = new FileOutputStream(gifFile)) {
                    byte[] b = new byte[8192]; int n; while ((n = in.read(b)) > 0) out.write(b, 0, n);
                }
                placeholderText.setVisibility(View.GONE);
                info.setText(gifDisplayName);
                status.setText("Loading preview...");
                convertButton.setEnabled(true);
                loadPreview();
            } catch (Exception e) { status.setText("Could not read GIF"); }
        } else if (requestCode == 2) {
            outputTree = data.getData();
            try { getContentResolver().takePersistableUriPermission(outputTree, data.getFlags() & (Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION)); } catch (Exception ignored) {}
            getPreferences(0).edit().putString("outputTree", outputTree.toString()).apply();
            folderValue.setText(outputTree.getLastPathSegment() != null ? outputTree.getLastPathSegment() : "Folder selected");
            Toast.makeText(this, "Folder saved", Toast.LENGTH_SHORT).show();
        } else if (requestCode == 3 && pendingOutput != null) {
            try (InputStream in = new FileInputStream(pendingOutput); OutputStream out = getContentResolver().openOutputStream(data.getData(), "w")) {
                if (out == null) throw new IOException("No writable output stream");
                byte[] b = new byte[8192]; int n; while ((n = in.read(b)) > 0) out.write(b, 0, n);
                status.setText("MCPACK saved");
            } catch (Exception e) { status.setText("Could not save MCPACK"); }
        }
    }

    void loadPreview() {
        try {
            byte[] raw = readAll(gifFile);
            firstPreview = BitmapFactory.decodeByteArray(raw, 0, raw.length);
            previewMovie = Movie.decodeByteArray(raw, 0, raw.length);
            if (firstPreview == null || previewMovie == null) throw new IOException("GIF decode failed");
            previewDuration = Math.max(100, previewMovie.duration());
            previewStep = 16;
            previewTime = 0;
            previewStartMs = SystemClock.uptimeMillis();
            int frames = countGifFrames(raw);
            String sizeStr = firstPreview.getWidth() + "x" + firstPreview.getHeight();
            info.setText(gifDisplayName + "  •  " + frames + " frames  •  " + sizeStr);
            status.setText("Ready to convert");
            handler.removeCallbacksAndMessages(null);
            handler.post(previewTick);
        } catch (Exception e) {
            status.setText("Could not read GIF");
        }
    }

    final Runnable previewTick = new Runnable() {
        @Override public void run() {
            if (previewMovie == null || firstPreview == null) return;
            int w = Math.max(1, preview.getWidth()), h = Math.max(1, preview.getHeight());
            Bitmap frame = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
            Canvas c = new Canvas(frame); Paint p = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.FILTER_BITMAP_FLAG);
            c.drawColor(Color.rgb(27,27,27));
            // Render each GIF frame on a fresh transparent layer. Drawing Movie
            // directly onto the previous composition makes Android retain
            // transparent/disposed pixels and produces the repeated-frame bug.
            Bitmap gifLayer = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
            Canvas gifCanvas = new Canvas(gifLayer);
            gifCanvas.drawColor(Color.TRANSPARENT, PorterDuff.Mode.CLEAR);
            previewTime = (int) ((SystemClock.uptimeMillis() - previewStartMs) % previewDuration);
            previewMovie.setTime(previewTime);
            int movieW = Math.max(1, previewMovie.width());
            int movieH = Math.max(1, previewMovie.height());
            gifCanvas.save();
            gifCanvas.scale((float) w / movieW, (float) h / movieH);
            previewMovie.draw(gifCanvas, 0, 0, p);
            gifCanvas.restore();
            c.drawBitmap(gifLayer, 0, 0, p);
            if (inventoryLines != null) c.drawBitmap(inventoryLines, null, new Rect(0,0,w,h), p);
            preview.setImageBitmap(frame);
            handler.postDelayed(this, previewStep);
        }
    };

    void convert() {
        if (gifFile == null) return;
        selectButton.setEnabled(false);
        convertButton.setEnabled(false);
        progress.setVisibility(View.VISIBLE);
        progress.setProgress(0);
        status.setText("Converting...");

        new Thread(() -> {
            try {
                final File out = makePack();
                runOnUiThread(() -> {
                    selectButton.setEnabled(true);
                    convertButton.setEnabled(true);
                    progress.setVisibility(View.GONE);
                    try { saveToSelectedFolder(out); }
                    catch (Exception e) { status.setText("Could not save MCPACK"); }
                });
            } catch (final Exception e) {
                runOnUiThread(() -> {
                    selectButton.setEnabled(true);
                    convertButton.setEnabled(true);
                    progress.setVisibility(View.GONE);
                    status.setText("Error: " + e.getMessage());
                });
            }
        }).start();
    }

    File makePack() throws Exception {
        byte[] raw = readAll(gifFile);
        android.graphics.Movie m = android.graphics.Movie.decodeByteArray(raw, 0, raw.length);
        if (m == null) throw new RuntimeException("Cannot decode GIF");
        int w = 352, h = 332;
        int gifW = Math.max(1, m.width());
        int gifH = Math.max(1, m.height());
        int total = countGifFrames(raw);
        int count = Math.max(1, Math.min(MAX_FLIPBOOK_FRAMES * MAX_FLIPBOOK_SEGMENTS, total));
        int dur = m.duration() > 0 ? m.duration() : count * 100;
        int fps = Math.max(2, Math.min(120, Math.round(1000f * count / dur)));

        Paint p = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.FILTER_BITMAP_FLAG);
        int segmentCount = (count + MAX_FLIPBOOK_FRAMES - 1) / MAX_FLIPBOOK_FRAMES;
        Map<String, Bitmap> sheets = new HashMap<>();
        for (int n = 0; n < count; n++) {
            int t = count == 1 ? 0 : (int) (dur * n / (float) (count - 1));
            m.setTime(t);
            int segment = n / MAX_FLIPBOOK_FRAMES;
            int local = n % MAX_FLIPBOOK_FRAMES;
            Bitmap sheet = sheets.get("" + segment);
            if (sheet == null) {
                sheet = Bitmap.createBitmap(w * Math.min(MAX_FLIPBOOK_FRAMES, count - segment * MAX_FLIPBOOK_FRAMES), h, Bitmap.Config.ARGB_8888);
                sheets.put("" + segment, sheet);
            }
            Bitmap frame = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
            Canvas frameCanvas = new Canvas(frame);
            frameCanvas.drawColor(Color.TRANSPARENT, PorterDuff.Mode.CLEAR);
            frameCanvas.save();
            frameCanvas.scale((float) w / gifW, (float) h / gifH);
            m.draw(frameCanvas, 0, 0, p);
            frameCanvas.restore();
            new Canvas(sheet).drawBitmap(frame, local * w, 0, p);
            frame.recycle();
            final int dn = n + 1;
            runOnUiThread(() -> {
                progress.setMax(count);
                progress.setProgress(dn);
            });
        }

        m.setTime(0);
        Bitmap packIcon = Bitmap.createBitmap(256, 256, Bitmap.Config.ARGB_8888);
        Canvas ic = new Canvas(packIcon);
        ic.scale(256f / gifW, 256f / gifH);
        m.draw(ic, 0, 0, p);
        ByteArrayOutputStream iconOut = new ByteArrayOutputStream();
        packIcon.compress(Bitmap.CompressFormat.PNG, 100, iconOut);

        Map<String, byte[]> files = new HashMap<>();
        loadAssets(files, "template", "");
        int[] segmentFrames = new int[segmentCount];
        for (int segment = 0; segment < segmentCount; segment++) {
            Bitmap sheet = sheets.get("" + segment);
            segmentFrames[segment] = Math.min(MAX_FLIPBOOK_FRAMES, count - segment * MAX_FLIPBOOK_FRAMES);
            ByteArrayOutputStream sheetOut = new ByteArrayOutputStream();
            sheet.compress(Bitmap.CompressFormat.PNG, 100, sheetOut);
            files.put("textures/ui/inventory_flipbook_" + String.format("%02d", segment) + ".png", sheetOut.toByteArray());
        }
        files.put("pack_icon.png", iconOut.toByteArray());
        JSONObject manifest = new JSONObject(new String(files.get("manifest.json"), "UTF-8"));
        JSONObject header = manifest.getJSONObject("header");
        String packTitle = sanitize(gifDisplayName.replaceFirst("(?i)\\.gif$", ""));
        header.put("name", packTitle);
        header.put("description", "Animated inventory from " + packTitle);
        files.put("manifest.json", manifest.toString(2).getBytes("UTF-8"));
        String common = patchSegmentedCommon(new String(files.get("ui/chouiui/chouiui_common.json"), "UTF-8"), segmentFrames, fps);
        files.put("ui/chouiui/chouiui_common.json", common.getBytes("UTF-8"));

        String name = sanitize(gifDisplayName.replaceFirst("(?i)\\.gif$", "")) + ".mcpack";
        File outDir = getExternalFilesDir(null);
        if (outDir == null) outDir = getCacheDir();
        //noinspection ResultOfMethodCallIgnored
        outDir.mkdirs();
        File outFile = new File(outDir, name);

        ByteArrayOutputStream zipOut = new ByteArrayOutputStream();
        ZipOutputStream z = new ZipOutputStream(zipOut);
        for (Map.Entry<String, byte[]> e : files.entrySet()) {
            z.putNextEntry(new ZipEntry(e.getKey()));
            z.write(e.getValue());
            z.closeEntry();
        }
        z.close();
        try (OutputStream fos = new FileOutputStream(outFile)) {
            fos.write(zipOut.toByteArray());
        }
        return outFile;
    }

    String patchSegmentedCommon(String raw, int[] segmentFrames, int fps) throws Exception {
        JSONObject root = new JSONObject(raw);
        root.remove("inventory_flipbook");
        JSONArray oldControls = root.getJSONObject("java_bg_animated").getJSONArray("controls");
        JSONObject lines = oldControls.getJSONObject(oldControls.length() - 1);
        JSONArray controls = new JSONArray();
        for (int i = 0; i < segmentFrames.length; i++) {
            String name = String.format("%02d", i);
            String anim = "segment_" + name;
            int next = (i + 1) % segmentFrames.length;
            String nextName = String.format("%02d", next);
            root.put("inventory_flipbook_" + name, new JSONObject()
                    .put("anim_type", "flip_book").put("initial_uv", new JSONArray().put(0).put(0))
                    .put("frame_count", segmentFrames[i]).put("frame_step", 352).put("fps", fps));
            root.put(anim + "_wait", new JSONObject().put("anim_type", "wait")
                    .put("duration", segmentFrames[i] / (double) Math.max(fps, 1))
                    .put("next", anim + "_hide"));
            root.put(anim + "_hide", new JSONObject().put("anim_type", "alpha")
                    .put("from", 1).put("to", 0).put("duration", 0.01)
                    .put("next", "segment_" + nextName + "_show"));
            root.put(anim + "_show", new JSONObject().put("anim_type", "alpha")
                    .put("from", 0).put("to", 1).put("duration", 0.01)
                    .put("next", anim + "_wait"));
            JSONObject image = new JSONObject().put("type", "image")
                    .put("texture", "textures/ui/inventory_flipbook_" + name)
                    .put("size", new JSONArray().put(176).put(166)).put("offset", new JSONArray().put(0).put(0))
                    .put("anchor_from", "top_left").put("anchor_to", "top_left").put("layer", 0)
                    .put("alpha", i == 0 ? 1 : 0).put("uv", "@chouiui.inventory_flipbook_" + name)
                    .put("uv_size", new JSONArray().put(352).put(332))
                    .put("anims", new JSONArray().put("@chouiui." + anim + (i == 0 ? "_wait" : "_show")))
                    .put("disable_anim_fast_forward", true);
            controls.put(new JSONObject().put("sheet_image_" + name, image));
        }
        controls.put(lines);
        root.getJSONObject("java_bg_animated").put("controls", controls);
        return root.toString(2);
    }


    void saveToSelectedFolder(File source) throws Exception {
        if (outputTree == null) {
            pendingOutput = source;
            Intent i = new Intent(Intent.ACTION_CREATE_DOCUMENT);
            i.setType("application/octet-stream");
            i.putExtra(Intent.EXTRA_TITLE, source.getName());
            startActivityForResult(i, 3);
            return;
        }
        Uri doc;
        try {
            doc = DocumentsContract.createDocument(getContentResolver(), outputTree, "application/zip", source.getName());
            if (doc == null) throw new IOException("Folder did not return a document");
        } catch (Exception e) {
            // Some file providers do not implement createDocument correctly.
            // Keep the selected folder as the preference but offer a reliable
            // document save fallback instead of silently reporting success.
            pendingOutput = source;
            Intent i = new Intent(Intent.ACTION_CREATE_DOCUMENT);
            i.setType("application/zip");
            i.putExtra(Intent.EXTRA_TITLE, source.getName());
            i.addCategory(Intent.CATEGORY_OPENABLE);
            startActivityForResult(i, 3);
            return;
        }
        try (InputStream in = new FileInputStream(source); OutputStream out = getContentResolver().openOutputStream(doc, "w")) {
            if (out == null) throw new IOException("No writable output stream");
            byte[] b = new byte[8192]; int n; while ((n = in.read(b)) > 0) out.write(b, 0, n);
        }
        status.setText("Saved: " + source.getName());
        Toast.makeText(this, "Saved " + source.getName(), Toast.LENGTH_LONG).show();
    }
    String displayNameFor(Uri uri) {
        try (Cursor c = getContentResolver().query(uri, new String[]{OpenableColumns.DISPLAY_NAME}, null, null, null)) {
            if (c != null && c.moveToFirst()) {
                String name = c.getString(0);
                if (name != null && !name.trim().isEmpty()) return name.replaceFirst("(?i)\\.gif$", "");
            }
        } catch (Exception ignored) {}
        String fallback = uri.getLastPathSegment();
        return sanitize(fallback == null ? "Animated Inventory" : fallback.replaceFirst("(?i)\\.gif$", ""));
    }

    static String sanitize(String s) {
        String cleaned = s.replaceAll("[^A-Za-z0-9 _-]", "").replaceAll("\\s+", " ").trim();
        if (cleaned.length() > 48) cleaned = cleaned.substring(0, 48);
        return cleaned.isEmpty() ? "Animated Inventory" : cleaned;
    }

    byte[] readAll(File f) throws Exception {
        java.io.InputStream in = new java.io.FileInputStream(f);
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        byte[] b = new byte[8192];
        int n;
        while ((n = in.read(b)) > 0) out.write(b, 0, n);
        in.close();
        return out.toByteArray();
    }

    int countGifFrames(byte[] raw) {
        // Skip GIF signature + logical screen descriptor + global colour table.
        // Starting at byte 0 makes the old parser stop at the header and return 1.
        if (raw == null || raw.length < 13) return 1;
        int i = 6, n = 0;
        int packed = raw[10] & 255;
        i = 13;
        if ((packed & 128) != 0) i += 3 * (1 << ((packed & 7) + 1));
        while (i < raw.length) {
            int b = raw[i++] & 255;
            if (b == 0x3b) break;
            if (b == 0x2c) {
                if (i + 9 > raw.length) break;
                int imagePacked = raw[i + 8] & 255;
                i += 9;
                if ((imagePacked & 128) != 0) i += 3 * (1 << ((imagePacked & 7) + 1));
                if (i >= raw.length) break;
                i++;
                while (i < raw.length) {
                    int s = raw[i++] & 255;
                    if (s == 0) break;
                    i += s;
                }
                n++;
            } else if (b == 0x21) {
                if (i >= raw.length) break;
                i++;
                while (i < raw.length) {
                    int s = raw[i++] & 255;
                    if (s == 0) break;
                    i += s;
                }
            } else break;
        }
        return Math.max(1, n);
    }

    void loadAssets(Map<String, byte[]> out, String root, String rel) throws Exception {
        String[] list = getAssets().list(root + (rel.isEmpty() ? "" : "/" + rel));
        if (list == null) return;
        for (String s : list) {
            String r = rel.isEmpty() ? s : rel + "/" + s;
            String p = root + "/" + r;
            String[] sub = getAssets().list(p);
            if (sub != null && sub.length > 0) {
                loadAssets(out, root, r);
            } else {
                try (java.io.InputStream in = getAssets().open(p)) {
                    ByteArrayOutputStream o = new ByteArrayOutputStream();
                    byte[] b = new byte[8192];
                    int n;
                    while ((n = in.read(b)) > 0) o.write(b, 0, n);
                    out.put(r, o.toByteArray());
                }
            }
        }
    }


    @Override protected void onDestroy() {
        super.onDestroy();
        handler.removeCallbacksAndMessages(null);
    }
}
