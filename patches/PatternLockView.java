package mx.crediagenda.app;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.view.MotionEvent;
import android.view.View;
import java.util.ArrayList;

/** Una cuadrícula 3×3; el trazado debe unir al menos cuatro puntos distintos. */
final class PatternLockView extends View {
    interface Listener { void onCompleted(String pattern); }
    private final Paint paint = new Paint(3);
    private final ArrayList<Integer> nodes = new ArrayList<>();
    private Listener listener;
    private float pointerX, pointerY;
    private boolean drawing = false;

    PatternLockView(Context c) {
        super(c);
        setBackgroundColor(Color.TRANSPARENT);
        setContentDescription("Dibuja tu patrón uniendo al menos cuatro puntos en una cuadrícula de 3 por 3");
    }
    void setListener(Listener next) { listener = next; }
    private float step() { return Math.min(getWidth(), getHeight()) / 3f; }
    private float x(int i) { return (i % 3 + 0.5f) * step() + (getWidth()-3f*step())/2f; }
    private float y(int i) { return (i / 3 + 0.5f) * step() + (getHeight()-3f*step())/2f; }
    private void tryPoint(float xx, float yy) {
        float max = step() * .36f;
        for (int i=0; i<9; i++) {
            float dx=xx-x(i),dy=yy-y(i);
            if (dx*dx+dy*dy <= max*max) {
                if (!nodes.contains(i)) {
                    if (!nodes.isEmpty()) {
                        int last=nodes.get(nodes.size()-1);
                        int r1=last/3, c1=last%3, r2=i/3, c2=i%3;
                        if ((Math.abs(r2-r1)==2 && Math.abs(c2-c1)!=1)
                           ||(Math.abs(c2-c1)==2 && Math.abs(r2-r1)!=1)) {
                            int mid=((r1+r2)/2)*3+(c1+c2)/2;
                            if (!nodes.contains(mid)) nodes.add(mid);
                        }
                    }
                    nodes.add(i);
                }
                break;
            }
        }
    }
    @Override public boolean onTouchEvent(MotionEvent e) {
        float px=e.getX(), py=e.getY();
        switch(e.getActionMasked()) {
            case MotionEvent.ACTION_DOWN:
                nodes.clear(); drawing=true;
                pointerX=px; pointerY=py;
                tryPoint(px,py); invalidate(); return true;
            case MotionEvent.ACTION_MOVE:
                for(int h=0; h<e.getHistorySize(); h++) tryPoint(e.getHistoricalX(h), e.getHistoricalY(h));
                tryPoint(px,py); pointerX=px; pointerY=py; invalidate(); return true;
            case MotionEvent.ACTION_UP:
                tryPoint(px,py); drawing=false;
                StringBuilder pattern = new StringBuilder();
                for(int id: nodes) pattern.append(id+1);
                nodes.clear(); invalidate();
                if(listener != null) listener.onCompleted(pattern.toString());
                return true;
            case MotionEvent.ACTION_CANCEL:
                nodes.clear(); drawing=false; invalidate(); return true;
        }
        return true;
    }
    @Override protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        paint.setColor(0xFF78A3F9);
        paint.setStrokeWidth(12f*getResources().getDisplayMetrics().density/3f);
        paint.setStrokeCap(Paint.Cap.ROUND);
        paint.setStyle(Paint.Style.STROKE);
        for(int p=1;p<nodes.size();p++) canvas.drawLine(x(nodes.get(p-1)),y(nodes.get(p-1)),x(nodes.get(p)),y(nodes.get(p)),paint);
        if (drawing && !nodes.isEmpty()) canvas.drawLine(x(nodes.get(nodes.size()-1)),y(nodes.get(nodes.size()-1)),pointerX,pointerY,paint);
        paint.setStyle(Paint.Style.FILL);
        for(int i=0;i<9;i++) {
            boolean selected=nodes.contains(i);
            paint.setColor(selected?0xFF376DD5:0xFFD5DEEC);
            canvas.drawCircle(x(i),y(i), selected?step()*.125f:step()*.092f,paint);
            paint.setColor(Color.WHITE);
            canvas.drawCircle(x(i),y(i),selected?step()*.052f:step()*.039f,paint);
        }
    }
}