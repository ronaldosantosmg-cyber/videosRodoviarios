using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.IO.Compression;
using System.Security.Cryptography;
using System.Text;
using System.Threading;
using System.Web.Script.Serialization;
using System.Windows.Forms;

class Instalador : Form {
    const string ManifestSHA = "@MANIFEST_SHA@";
    TextBox path = new TextBox(), details = new TextBox();
    Label status = new Label(); ProgressBar progress = new ProgressBar();
    Button install = new Button(), cancel = new Button(), browse = new Button(), open = new Button();
    volatile bool busy, cancelled; string cancelFile, logFile, destination;
    static JavaScriptSerializer json = new JavaScriptSerializer();
    [STAThread] static void Main(string[] args) {
        Application.EnableVisualStyles(); Application.SetCompatibleTextRenderingDefault(false);
        var form = new Instalador();
        if (args.Length == 2 && args[0] == "--capturar") form.Shown += delegate {
            var timer = new System.Windows.Forms.Timer(); timer.Interval=300;
            timer.Tick += delegate { timer.Stop(); using(var image=new Bitmap(form.Width,form.Height)) {form.DrawToBitmap(image,form.ClientRectangle);image.Save(args[1]);} form.Close();}; timer.Start();
        };
        Application.Run(form);
    }
    Instalador() {
        Text="Instalar Rodovia Studio 2.02 — Ronaldo Santos"; Width=780; Height=570; MinimumSize=new Size(650,500);
        StartPosition=FormStartPosition.CenterScreen; Font=new Font("Segoe UI",10); AutoScaleMode=AutoScaleMode.Dpi;
        BackColor=Color.White;
        var layout=new TableLayoutPanel {Dock=DockStyle.Fill,Padding=new Padding(22),ColumnCount=2,RowCount=9};
        layout.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));layout.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute,110));
        var title=new Label {Text="Rodovia Studio 2.02",AutoSize=true,Font=new Font("Segoe UI",21,FontStyle.Bold),ForeColor=Color.FromArgb(15,75,117)};
        layout.Controls.Add(title,0,0);layout.SetColumnSpan(title,2);
        var description=new Label {Text="Instalação nova • Windows x64\nFabricante: Ronaldo Santos",AutoSize=true,Margin=new Padding(0,8,0,10)};
        layout.Controls.Add(description,0,1);layout.SetColumnSpan(description,2);
        var notice=new Label {Text="Inclui o aplicativo e Python. A primeira instalação baixa bibliotecas verificadas e FFmpeg.\nNecessita internet e 3 GiB livres. A pasta escolhida deve ser nova.\n@SIGNING_NOTICE@",AutoSize=true,Margin=new Padding(0,0,0,14)};
        layout.Controls.Add(notice,0,2);layout.SetColumnSpan(notice,2);
        path.Text=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"Ronaldo Santos","Rodovia Studio");path.Dock=DockStyle.Fill;
        browse.Text="Escolher…";browse.Dock=DockStyle.Fill;browse.Click+=delegate {using(var d=new FolderBrowserDialog()){d.Description="Escolha a pasta PAI; será criada uma subpasta nova Rodovia Studio.";if(d.ShowDialog()==DialogResult.OK)path.Text=Path.Combine(d.SelectedPath,"Rodovia Studio");}};
        layout.Controls.Add(path,0,3);layout.Controls.Add(browse,1,3);
        status.Text="Pronto para instalar. Instalações existentes não serão sobrescritas.";status.AutoSize=true;status.Margin=new Padding(0,14,0,6);layout.Controls.Add(status,0,4);layout.SetColumnSpan(status,2);
        progress.Dock=DockStyle.Fill;layout.Controls.Add(progress,0,5);layout.SetColumnSpan(progress,2);
        details.Multiline=true;details.ReadOnly=true;details.ScrollBars=ScrollBars.Vertical;details.Dock=DockStyle.Fill;details.BackColor=Color.FromArgb(246,248,250);layout.Controls.Add(details,0,6);layout.SetColumnSpan(details,2);layout.RowStyles.Add(new RowStyle());
        for(int i=1;i<6;i++)layout.RowStyles.Add(new RowStyle());layout.RowStyles.Add(new RowStyle(SizeType.Percent,100));
        var buttons=new FlowLayoutPanel {AutoSize=true,Dock=DockStyle.Fill,FlowDirection=FlowDirection.RightToLeft,Padding=new Padding(0,12,0,0)};
        install.Text="Instalar";install.AutoSize=true;install.BackColor=Color.FromArgb(15,94,153);install.ForeColor=Color.White;install.Click+=Start;
        cancel.Text="Fechar";cancel.AutoSize=true;cancel.Click+=delegate {if(busy)Cancel();else Close();};
        open.Text="Abrir pasta";open.AutoSize=true;open.Enabled=false;open.Click+=delegate {Process.Start(new ProcessStartInfo(destination){UseShellExecute=true});};
        buttons.Controls.Add(install);buttons.Controls.Add(cancel);buttons.Controls.Add(open);layout.Controls.Add(buttons,0,7);layout.SetColumnSpan(buttons,2);
        Controls.Add(layout);FormClosing+=delegate(object sender,FormClosingEventArgs e){if(busy){e.Cancel=true;Cancel();}};
    }
    void UI(Action action){if(!IsDisposed)BeginInvoke(action);}
    void Cancel(){cancelled=true;if(cancelFile!=null)try{File.WriteAllText(cancelFile,"cancelar");}catch(IOException){}cancel.Enabled=false;status.Text="Cancelando: aguarde a operação atual liberar os arquivos…";}
    void Report(string message) {
        lock(this) {if(logFile!=null)File.AppendAllText(logFile,message+Environment.NewLine,Encoding.UTF8);}
        UI(delegate {try {var data=json.Deserialize<Dictionary<string,object>>(message);status.Text=Convert.ToString(data["stage"]);if(data["percent"]==null)progress.Style=ProgressBarStyle.Marquee;else {progress.Style=ProgressBarStyle.Continuous;progress.Value=Math.Max(0,Math.Min(100,(int)Convert.ToDouble(data["percent"])));}}catch {status.Text=message;}
            details.AppendText(message+Environment.NewLine);});
    }
    static string Hash(string f){using(var h=SHA256.Create())using(var s=File.OpenRead(f))return BitConverter.ToString(h.ComputeHash(s)).Replace("-","").ToLowerInvariant();}
    static string Q(string s){var b=new StringBuilder("\"");int slash=0;foreach(char c in s){if(c=='\\'){slash++;continue;}if(c=='"'){b.Append('\\',slash*2+1);b.Append(c);}else{b.Append('\\',slash);b.Append(c);}slash=0;}b.Append('\\',slash*2);b.Append('"');return b.ToString();}
    static string Local(string root,string name) {
        if(name.IndexOf('\\')>=0 || name.IndexOf(':')>=0 || Path.IsPathRooted(name))throw new Exception("Caminho inválido no pacote.");
        foreach(string part in name.Split('/'))if(part=="..")throw new Exception("Caminho fora do pacote.");
        return Path.Combine(root,name.Replace('/',Path.DirectorySeparatorChar));
    }
    void Start(object sender,EventArgs args) {
        if(Environment.OSVersion.Platform!=PlatformID.Win32NT || !Environment.Is64BitOperatingSystem){MessageBox.Show("Use Windows 10/11 x64.");return;}
        try{destination=Path.GetFullPath(path.Text.Trim());}catch(Exception e){MessageBox.Show("Pasta inválida: "+e.Message);return;}
        if(Directory.Exists(destination)||File.Exists(destination)){MessageBox.Show("Escolha uma pasta nova. Os dados existentes não serão sobrescritos.");return;}
        busy=true;cancelled=false;install.Enabled=false;browse.Enabled=false;path.Enabled=false;cancel.Text="Cancelar";progress.Style=ProgressBarStyle.Marquee;
        string logs=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"Ronaldo Santos","Logs");Directory.CreateDirectory(logs);
        logFile=Path.Combine(logs,"instalacao-"+DateTime.Now.ToString("yyyyMMdd-HHmmss")+"-"+Guid.NewGuid().ToString("N")+".log");
        new Thread(Work){IsBackground=true}.Start();
    }
    void Work() {
        string temp=null;bool success=false;
        try {
            string root=AppDomain.CurrentDomain.BaseDirectory,manifest=Path.Combine(root,"distribuicao.json");
            if(Hash(manifest)!=ManifestSHA)throw new Exception("Manifesto alterado. Baixe o pacote completo novamente.");
            var m=json.Deserialize<Dictionary<string,object>>(File.ReadAllText(manifest,Encoding.UTF8));
            Report("Conferindo integridade do pacote");
            foreach(var pair in (Dictionary<string,object>)m["files"]){if(cancelled)throw new Exception("Instalação cancelada.");if(Hash(Local(root,pair.Key))!=Convert.ToString(pair.Value))throw new Exception("Arquivo ausente ou alterado: "+pair.Key);}
            temp=Path.Combine(Path.GetTempPath(),"RodoviaSetup-"+Guid.NewGuid().ToString("N"));Directory.CreateDirectory(temp);cancelFile=Path.Combine(temp,"cancelar.flag");
            string pythonRoot=Path.Combine(temp,"python");Directory.CreateDirectory(pythonRoot);
            using(var zip=ZipFile.OpenRead(Path.Combine(root,"payload/python.nupkg")))foreach(var entry in zip.Entries){
                if(cancelled)throw new Exception("Instalação cancelada.");if(!entry.FullName.StartsWith("tools/",StringComparison.Ordinal))continue;
                string name=entry.FullName.Substring(6);if(name.Length==0)continue;string file=Local(pythonRoot,name);
                if(name.EndsWith("/")){Directory.CreateDirectory(file);continue;}Directory.CreateDirectory(Path.GetDirectoryName(file));entry.ExtractToFile(file,false);
            }
            if(cancelled)throw new Exception("Instalação cancelada.");
            var info=new ProcessStartInfo(Path.Combine(pythonRoot,"python.exe"),"-X utf8 "+Q(Path.Combine(root,"instalar.py"))+" --raiz "+Q(root)+" --destino "+Q(destination)+" --manifest-sha "+ManifestSHA+" --cancelar "+Q(cancelFile));
            info.UseShellExecute=false;info.CreateNoWindow=true;info.RedirectStandardOutput=true;info.RedirectStandardError=true;info.StandardOutputEncoding=Encoding.UTF8;info.StandardErrorEncoding=Encoding.UTF8;
            using(var p=new Process()){p.StartInfo=info;p.OutputDataReceived+=delegate(object s,DataReceivedEventArgs e){if(e.Data!=null)Report(e.Data);};p.ErrorDataReceived+=delegate(object s,DataReceivedEventArgs e){if(e.Data!=null)Report(e.Data);};p.Start();p.BeginOutputReadLine();p.BeginErrorReadLine();p.WaitForExit();if(p.ExitCode!=0)throw new Exception(p.ExitCode==2?"Instalação cancelada.":"Instalação não concluída. Veja os detalhes e o log.");}
            success=true;Report("Instalação concluída. Abra Rodovia Studio.exe na pasta escolhida.");
        }catch(Exception e){Report(e.Message+"\nLog: "+logFile);}
        finally {if(temp!=null)try{Directory.Delete(temp,true);}catch{}busy=false;UI(delegate{progress.Style=ProgressBarStyle.Continuous;progress.Value=success?100:0;cancel.Text="Fechar";cancel.Enabled=true;open.Enabled=success;install.Enabled=!success;browse.Enabled=!success;path.Enabled=!success;});}
    }
}
