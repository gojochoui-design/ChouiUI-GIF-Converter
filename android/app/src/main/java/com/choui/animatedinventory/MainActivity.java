package com.choui.animatedinventory;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.provider.DocumentsContract;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Color;
import android.graphics.Movie;
import android.graphics.Rect;
import android.graphics.drawable.Drawable;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
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

public class MainActivity extends Activity {

    static final int REQ_PERM = 7;

    File gifFile;
    File pendingOutput;
    Uri outputTree;

    ImageView preview;
    TextView info, status, folderValue, placeholderText;
    android.widget.Button selectButton, convertButton, folderButton;
    ProgressBar progress;
    final Handler handler = new Handler(Looper.getMainLooper());
    Movie previewMovie;
    Bitmap firstPreview, inventoryBase, inventoryLines;
    int previewTime=0, previewDuration=100, previewStep=100;

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
                try (InputStream in = getContentResolver().openInputStream(u); OutputStream out = new FileOutputStream(gifFile)) {
                    byte[] b = new byte[8192]; int n; while ((n = in.read(b)) > 0) out.write(b, 0, n);
                }
                placeholderText.setVisibility(View.GONE);
                info.setText(gifFile.getName());
                status.setText("Loading preview...");
                convertButton.setEnabled(true);
                loadPreview();
            } catch (Exception e) { status.setText("Could not read GIF"); }
        } else if (requestCode == 2) {
            outputTree = data.getData();
            try { getContentResolver().takePersistableUriPermission(outputTree, data.getFlags() & (Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION)); } catch (Exception ignored) {}
            getPreferences(0).edit().putString("outputTree", outputTree.toString()).apply();
            folderValue.setText("Folder selected");
            Toast.makeText(this, "Folder saved", Toast.LENGTH_SHORT).show();
        } else if (requestCode == 3 && pendingOutput != null) {
            try (InputStream in = new FileInputStream(pendingOutput); OutputStream out = getContentResolver().openOutputStream(data.getData())) {
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
            previewStep = Math.max(16, previewDuration / Math.max(1, countGifFrames(raw)));
            previewTime = 0;
            int frames = countGifFrames(raw);
            String sizeStr = firstPreview.getWidth() + "x" + firstPreview.getHeight();
            info.setText(gifFile.getName() + "  •  " + frames + " frames  •  " + sizeStr);
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
            if (inventoryBase != null) c.drawBitmap(inventoryBase, null, new Rect(0,0,w,h), p);
            previewMovie.setTime(previewTime);
            int movieW = Math.max(1, previewMovie.width());
            int movieH = Math.max(1, previewMovie.height());
            c.save();
            c.scale((float) w / movieW, (float) h / movieH);
            previewMovie.draw(c, 0, 0, p);
            c.restore();
            if (inventoryLines != null) c.drawBitmap(inventoryLines, null, new Rect(0,0,w,h), p);
            preview.setImageBitmap(frame);
            previewTime = (previewTime + previewStep) % previewDuration;
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
                    try { saveToSelectedFolder(out); status.setText("Saved: " + out.getName()); }
                    catch (Exception e) { status.setText("Could not save MCPACK"); }
                    Toast.makeText(MainActivity.this, "MCPACK ready", Toast.LENGTH_LONG).show();
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
        int count = Math.max(1, total);
        int dur = m.duration() > 0 ? m.duration() : count * 100;
        int fps = Math.max(2, Math.min(30, Math.round(1000f * count / dur)));

        Bitmap strip = Bitmap.createBitmap(w * count, h, Bitmap.Config.ARGB_8888);
        Canvas c = new Canvas(strip);
        Paint p = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.FILTER_BITMAP_FLAG);
        for (int n = 0; n < count; n++) {
            int t = (int) (dur * n / (float) count);
            m.setTime(t);
            c.save();
            c.scale((float) w / gifW, (float) h / gifH);
            m.draw(c, 0, 0, p);
            c.restore();
            final int dn = n + 1;
            runOnUiThread(() -> {
                progress.setMax(count);
                progress.setProgress(dn);
            });
        }

        ByteArrayOutputStream stripOut = new ByteArrayOutputStream();
        strip.compress(Bitmap.CompressFormat.PNG, 100, stripOut);

        m.setTime(0);
        Bitmap packIcon = Bitmap.createBitmap(256, 256, Bitmap.Config.ARGB_8888);
        Canvas ic = new Canvas(packIcon);
        ic.scale(256f / gifW, 256f / gifH);
        m.draw(ic, 0, 0, p);
        ByteArrayOutputStream iconOut = new ByteArrayOutputStream();
        packIcon.compress(Bitmap.CompressFormat.PNG, 100, iconOut);

        Map<String, byte[]> files = new HashMap<>();
        loadAssets(files, "template", "");
        files.put("textures/ui/inventory_flipbook.png", stripOut.toByteArray());
        files.put("pack_icon.png", iconOut.toByteArray());

        String common = new String(files.get("ui/chouiui/chouiui_common.json"), "UTF-8")
                .replaceAll("\\\"frame_count\\\"\\s*:\\s*\\d+", "\"frame_count\": " + count)
                .replaceAll("\\\"fps\\\"\\s*:\\s*\\d+", "\"fps\": " + fps);
        files.put("ui/chouiui/chouiui_common.json", common.getBytes("UTF-8"));

        String name = sanitize(gifFile.getName().replaceFirst("(?i)\\.gif$", "")) + ".mcpack";
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


    void saveToSelectedFolder(File source) throws Exception {
        if (outputTree == null) {
            pendingOutput = source;
            Intent i = new Intent(Intent.ACTION_CREATE_DOCUMENT);
            i.setType("application/octet-stream");
            i.putExtra(Intent.EXTRA_TITLE, source.getName());
            startActivityForResult(i, 3);
            return;
        }
        Uri doc = DocumentsContract.createDocument(getContentResolver(), outputTree, "application/octet-stream", source.getName());
        try (InputStream in = new FileInputStream(source); OutputStream out = getContentResolver().openOutputStream(doc)) {
            byte[] b = new byte[8192]; int n; while ((n = in.read(b)) > 0) out.write(b, 0, n);
        }
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
        int i = 0, n = 0;
        while (i < raw.length) {
            int b = raw[i++] & 255;
            if (b == 0x3b) break;
            if (b == 0x2c) {
                if (i + 9 > raw.length) break;
                int packed = raw[i + 8] & 255;
                i += 9;
                if ((packed & 128) != 0) i += 3 * (1 << ((packed & 7) + 1));
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
