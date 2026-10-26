using System;
using System.Drawing;
using System.IO;
using System.Windows.Forms;
using RodoviaStudioLauncher;

class SplashValidation
{
    [STAThread]
    static int Main(string[] args)
    {
        Application.EnableVisualStyles();
        using (Icon icon = new Icon(args[0]))
        using (Splash splash = new Splash(icon, "1.42.23"))
        {
            splash.Show(); splash.Status("Validando atualização e preparando o aplicativo…");
            splash.RestartAnimation(); Bitmap initial = Capture(splash);
            Pump(250);
            string text = "";
            foreach (Control c in splash.Controls) text += c.Text + "\n";
            if (!text.Contains("Versão 1.42.23") || !text.Contains("Fabricante: Ronaldo Santos")) return 1;
            Bitmap a = Capture(splash); Pump(450); Bitmap b = Capture(splash);
            Directory.CreateDirectory(args[1]);
            a.Save(Path.Combine(args[1], "splash_142_1_a.png"));
            b.Save(Path.Combine(args[1], "splash_142_1_b.png"));
            int changed = 0;
            for (int y=30; y<145; y++) for (int x=22; x<140; x++)
                if (a.GetPixel(x,y) != b.GetPixel(x,y)) changed++;
            a.Dispose(); b.Dispose();
            if (changed < 100) { Console.WriteLine("Logo não animou: "+changed); return 2; }
            splash.FinishAnimation(); Bitmap final = Capture(splash); int poseDifference = 0;
            for (int y=30; y<145; y++) for (int x=22; x<140; x++)
                if (initial.GetPixel(x,y) != final.GetPixel(x,y)) poseDifference++;
            initial.Dispose(); final.Dispose();
            if (poseDifference != 0) { Console.WriteLine("Logo não voltou à posição inicial: "+poseDifference); return 3; }
            splash.Close(); Console.WriteLine("Splash: versão, fabricante e animação verificados ("+changed+" pixels alterados).");
        }
        return 0;
    }
    static void Pump(int ms)
    {
        DateTime end=DateTime.UtcNow.AddMilliseconds(ms);
        while(DateTime.UtcNow < end) { Application.DoEvents(); System.Threading.Thread.Sleep(15); }
    }
    static Bitmap Capture(Form f)
    {
        Bitmap b=new Bitmap(f.Width,f.Height); f.DrawToBitmap(b,new Rectangle(0,0,f.Width,f.Height)); return b;
    }
}
