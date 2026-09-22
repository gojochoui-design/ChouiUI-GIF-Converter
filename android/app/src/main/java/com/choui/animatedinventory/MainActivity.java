package com.choui.animatedinventory;

import android.app.*;
import android.os.*;
import android.content.*;
import android.graphics.*;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.provider.DocumentsContract;
import android.view.*;
import android.widget.*;
import java.io.*;
import java.util.*;
import java.util.zip.*;

public class MainActivity extends Activity {
  static final int PICK=1, FOLDER=2, SAVE=3;
  Uri gif, outputTree;
  byte[] result;
  TextView status, info, folderValue;
  Button action;
  ProgressBar progress;
  ImageView preview;
  Movie movie;
  Bitmap firstFrame, lines;
  final Handler handler = new Handler(Looper.getMainLooper());
  int time=0, duration=100, step=100;
  final int bg=Color.rgb(20,20,20), text=Color.rgb(235,235,235), dim=Color.rgb(165,165,165), panel=Color.rgb(38,38,38), accent=Color.rgb(88,88,88);

  int dp(int v){ return (int)(v*getResources().getDisplayMetrics().density+0.5f); }
  TextView label(String s,float size,int color){ TextView t=new TextView(this); t.setText(s); t.setTextSize(size); t.setTextColor(color); return t; }
  GradientDrawable shape(int color,int radius){ GradientDrawable g=new GradientDrawable(); g.setColor(color); g.setCornerRadius(dp(radius)); return g; }
  Button button(String s){ Button b=new Button(this); b.setText(s); b.setTextSize(13); b.setTextColor(Color.WHITE); b.setTypeface(null,1); b.setAllCaps(false); b.setMinHeight(0); b.setPadding(dp(16),0,dp(16),0); b.setBackground(shape(Color.rgb(55,55,55),10)); return b; }

  @Override public void onCreate(Bundle state){
    super.onCreate(state);
    outputTree = Uri.parse(getPreferences(0).getString("outputTree",""));
    if(outputTree.toString().isEmpty()) outputTree=null;
    try{ lines=BitmapFactory.decodeStream(getAssets().open("template/textures/ui/inventory_lines.png")); }catch(Exception ignored){}
    buildUi();
  }

  void buildUi(){
    ScrollView scroll=new ScrollView(this); scroll.setBackgroundColor(bg);
    LinearLayout box=new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setGravity(Gravity.CENTER_HORIZONTAL); box.setPadding(dp(22),dp(20),dp(22),dp(28)); scroll.addView(box);
    LinearLayout top=new LinearLayout(this); top.setGravity(Gravity.CENTER_VERTICAL); top.setPadding(0,0,0,dp(8));
    TextView title=label("CHOUIUI  •  GIF CONVERTER",19,text); title.setTypeface(null,1); top.addView(title,new LinearLayout.LayoutParams(0,dp(52),1));
    ImageButton gear=new ImageButton(this); gear.setImageResource(R.drawable.ic_gear); gear.setBackgroundColor(Color.TRANSPARENT); gear.setContentDescription("Export folder"); gear.setPadding(dp(13),dp(13),dp(13),dp(13)); gear.setOnClickListener(v->showFolderPanel()); top.addView(gear,new LinearLayout.LayoutParams(dp(54),dp(52))); box.addView(top,new LinearLayout.LayoutParams(-1,dp(60)));
    TextView sub=label("Animated player inventory for Minecraft Bedrock",13,dim); sub.setGravity(Gravity.CENTER); box.addView(sub,new LinearLayout.LayoutParams(-1,dp(38)));
    preview=new ImageView(this); preview.setScaleType(ImageView.ScaleType.FIT_XY); preview.setBackgroundColor(Color.rgb(224,224,224)); LinearLayout.LayoutParams pp=new LinearLayout.LayoutParams(dp(352),dp(300)); pp.topMargin=dp(8); pp.bottomMargin=dp(14); box.addView(preview,pp);
    action=button("SELECT GIF"); box.addView(action,new LinearLayout.LayoutParams(dp(330),dp(54))); action.setOnClickListener(v->{ if(gif==null) pickGif(); else convert(); });
    info=label("No GIF selected",13,dim); info.setGravity(Gravity.CENTER); box.addView(info,new LinearLayout.LayoutParams(dp(330),dp(42)));
    progress=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal); progress.setVisibility(View.INVISIBLE); box.addView(progress,new LinearLayout.LayoutParams(dp(330),dp(8)));
    status=label("Waiting for a GIF",12,dim); status.setGravity(Gravity.CENTER); box.addView(status,new LinearLayout.LayoutParams(dp(330),dp(38)));
    setContentView(scroll);
  }

  void showFolderPanel(){
    LinearLayout box=new LinearLayout(this); box.setOrientation(LinearLayout.VERTICAL); box.setPadding(dp(20),dp(6),dp(20),0);
    TextView note=label("Choose the folder where MCPACK files will be exported.",13,dim); note.setPadding(0,0,0,dp(12)); box.addView(note);
    folderValue=label(outputTree==null?"No folder selected":"Folder access granted",13,text); folderValue.setPadding(dp(12),dp(12),dp(12),dp(12)); folderValue.setBackground(shape(Color.rgb(45,45,45),8)); box.addView(folderValue);
    AlertDialog d=new AlertDialog.Builder(this).setTitle("Export folder").setView(box).setNegativeButton("Close",null).setPositiveButton("Choose folder",null).create();
    d.setOnShowListener(x->d.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v->{d.dismiss(); chooseFolder();})); d.show();
  }

  void pickGif(){ Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT); i.setType("image/*"); i.putExtra(Intent.EXTRA_MIME_TYPES,new String[]{"image/gif","image/*"}); i.addCategory(Intent.CATEGORY_OPENABLE); i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION); startActivityForResult(i,PICK); }
  void chooseFolder(){ Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE); i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_WRITE_URI_PERMISSION|Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION); startActivityForResult(i,FOLDER); }

  @Override protected void onActivityResult(int req,int resultCode,Intent data){ super.onActivityResult(req,resultCode,data); if(resultCode!=RESULT_OK||data==null)return;
    if(req==PICK){ gif=data.getData(); try{getContentResolver().takePersistableUriPermission(gif,data.getFlags()&(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_WRITE_URI_PERMISSION));}catch(Exception ignored){} action.setText("CONVERT GIF"); info.setText("GIF selected"); status.setText("Loading preview..."); new Thread(()->loadPreview()).start(); }
    else if(req==FOLDER){ outputTree=data.getData(); try{getContentResolver().takePersistableUriPermission(outputTree,data.getFlags()&(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_WRITE_URI_PERMISSION));}catch(Exception ignored){} getPreferences(0).edit().putString("outputTree",outputTree.toString()).apply(); status.setText("Export folder selected"); }
    else if(req==SAVE){ try(OutputStream out=getContentResolver().openOutputStream(data.getData())){out.write(this.result);status.setText("MCPACK saved");}catch(Exception e){status.setText("Could not save MCPACK");} }
  }

  void loadPreview(){ try{ byte[] raw=read(gif); Bitmap first=BitmapFactory.decodeByteArray(raw,0,raw.length); runOnUiThread(()->setupPreview(raw,first)); }catch(Exception e){runOnUiThread(()->status.setText("Could not read GIF"));} }
  void setupPreview(byte[] raw,Bitmap first){ try{ if(first==null)throw new IOException(); firstFrame=first; movie=Movie.decodeByteArray(raw,0,raw.length); if(movie==null)throw new IOException(); duration=Math.max(100,movie.duration()); step=Math.max(16,duration/Math.max(1,gifFrames(raw))); time=0; status.setText("Ready"); handler.removeCallbacksAndMessages(null); handler.post(previewTick); }catch(Exception e){ if(first!=null){preview.setImageBitmap(first);status.setText("Ready (first frame)");}else status.setText("Could not read GIF"); } }
  Runnable previewTick=new Runnable(){public void run(){ if(movie==null)return; int w=Math.max(1,preview.getWidth()),h=Math.max(1,preview.getHeight()); Bitmap b=Bitmap.createBitmap(w,h,Bitmap.Config.ARGB_8888); Canvas c=new Canvas(b); c.drawColor(Color.rgb(224,224,224)); Paint p=new Paint(Paint.ANTI_ALIAS_FLAG); if(firstFrame!=null)c.drawBitmap(firstFrame,null,new Rect(0,0,w,h),p); movie.setTime(time); movie.draw(c,0,0,p); if(lines!=null)c.drawBitmap(lines,null,new Rect(0,0,w,h),p); preview.setImageBitmap(b); time=(time+step)%duration; handler.postDelayed(this,step); }};

  void convert(){ new ConvertTask().execute(); }
  class ConvertTask extends AsyncTask<Void,Void,byte[]>{ protected void onPreExecute(){action.setEnabled(false);progress.setVisibility(View.VISIBLE);status.setText("Converting...");} protected byte[] doInBackground(Void...v){try{return makePack();}catch(Exception e){return null;}} protected void onPostExecute(byte[] b){action.setEnabled(true);progress.setVisibility(View.INVISIBLE);if(b==null){status.setText("Could not convert GIF");return;}result=b;try{saveResult();}catch(Exception e){status.setText("Could not save MCPACK");}} }
  void saveResult()throws Exception{String name="Animated Inventory.mcpack";if(outputTree==null){Intent i=new Intent(Intent.ACTION_CREATE_DOCUMENT);i.setType("application/octet-stream");i.putExtra(Intent.EXTRA_TITLE,name);startActivityForResult(i,SAVE);return;}try{Uri doc=DocumentsContract.createDocument(getContentResolver(),outputTree,"application/octet-stream",name);try(OutputStream out=getContentResolver().openOutputStream(doc)){out.write(result);}status.setText("MCPACK saved");}catch(Exception e){outputTree=null;getPreferences(0).edit().remove("outputTree").apply();Intent i=new Intent(Intent.ACTION_CREATE_DOCUMENT);i.setType("application/octet-stream");i.putExtra(Intent.EXTRA_TITLE,name);startActivityForResult(i,SAVE);}}
  byte[] read(Uri u)throws Exception{InputStream in=getContentResolver().openInputStream(u);ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] b=new byte[8192];int n;while((n=in.read(b))>0)out.write(b,0,n);in.close();return out.toByteArray();}
  int gifFrames(byte[] raw){int i=0,n=0;while(i<raw.length){int b=raw[i++]&255;if(b==0x3b)break;if(b==0x2c){if(i+9>raw.length)break;int packed=raw[i+8]&255;i+=9;if((packed&128)!=0)i+=3*(1<<((packed&7)+1));if(i>=raw.length)break;i++;while(i<raw.length){int s=raw[i++]&255;if(s==0)break;i+=s;}n++;}else if(b==0x21){if(i>=raw.length)break;i++;while(i<raw.length){int s=raw[i++]&255;if(s==0)break;i+=s;}}else break;}return Math.max(1,n);}
  byte[] makePack()throws Exception{byte[] raw=read(gif);Movie m=Movie.decodeByteArray(raw,0,raw.length);if(m==null)throw new Exception();int count=Math.min(11,gifFrames(raw)),dur=Math.max(100,m.duration()),fps=Math.max(2,Math.min(30,Math.round(1000f*count/dur))),w=352,h=332;Bitmap strip=Bitmap.createBitmap(w*count,h,Bitmap.Config.ARGB_8888);Canvas c=new Canvas(strip);Paint p=new Paint(3);for(int n=0;n<count;n++){m.setTime((int)(dur*n/(float)count));c.save();c.scale((float)w/m.width(),(float)h/m.height());m.draw(c,0,0,p);c.restore();}Bitmap lines=BitmapFactory.decodeStream(getAssets().open("template/textures/ui/inventory_lines.png"));for(int n=0;n<count;n++)c.drawBitmap(lines,null,new Rect(n*w,0,n*w+w,h),p);ByteArrayOutputStream stripOut=new ByteArrayOutputStream();strip.compress(Bitmap.CompressFormat.PNG,100,stripOut);Bitmap packIcon=Bitmap.createBitmap(256,256,Bitmap.Config.ARGB_8888);Canvas ic=new Canvas(packIcon);m.setTime(0);ic.scale(256f/m.width(),256f/m.height());m.draw(ic,0,0,p);ByteArrayOutputStream iconOut=new ByteArrayOutputStream();packIcon.compress(Bitmap.CompressFormat.PNG,100,iconOut);Map<String,byte[]> files=new HashMap<>();loadAssets(files,"template","");files.put("textures/ui/inventory_flipbook.png",stripOut.toByteArray());files.put("pack_icon.png",iconOut.toByteArray());String common=new String(files.get("ui/chouiui/chouiui_common.json"),"UTF-8").replaceAll("\\\"frame_count\\\"\\s*:\\s*\\d+","\\\"frame_count\\\": "+count).replaceAll("\\\"fps\\\"\\s*:\\s*\\d+","\\\"fps\\\": "+fps);files.put("ui/chouiui/chouiui_common.json",common.getBytes("UTF-8"));ByteArrayOutputStream out=new ByteArrayOutputStream();ZipOutputStream z=new ZipOutputStream(out);for(Map.Entry<String,byte[]>e:files.entrySet()){z.putNextEntry(new ZipEntry(e.getKey()));z.write(e.getValue());z.closeEntry();}z.close();return out.toByteArray();}
  void loadAssets(Map<String,byte[]>out,String root,String rel)throws Exception{String[] list=getAssets().list(root+(rel.isEmpty()?"":"/"+rel));for(String s:list){String r=rel.isEmpty()?s:rel+"/"+s,p=root+"/"+r;String[] sub=getAssets().list(p);if(sub.length>0)loadAssets(out,root,r);else{InputStream in=getAssets().open(p);ByteArrayOutputStream o=new ByteArrayOutputStream();byte[]b=new byte[8192];int n;while((n=in.read(b))>0)o.write(b,0,n);out.put(r,o.toByteArray());}}}
}
