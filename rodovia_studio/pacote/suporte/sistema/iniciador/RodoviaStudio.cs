// Rodovia Studio — iniciador para Windows (.exe).
//
// O executável é pequeno e quase nunca muda: ele só prepara, atualiza, inicia e encerra o aplicativo.
// Os comandos e todo o programa continuam em arquivos separados (sistema\programa\app, .py/.js/.html),
// trocados pelos ZIPs de atualização. Assim não é preciso refazer o .exe a cada versão.
//
// Compilado no próprio Windows pelo compilador do .NET Framework 4 (COMPILAR INICIADOR.cmd), sem
// administrador. Escrito em C# 5 (o csc.exe do .NET Framework não aceita recursos mais novos).
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.IO;
using System.Net;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Windows.Forms;
using System.Runtime.CompilerServices;

namespace RodoviaStudioLauncher
{
    static class Program
    {
        public const string Version = "1.4";

        [STAThread]
        static void Main(string[] args)
        {
#if WEBVIEW2
            // 1.1: as DLLs do WebView2 ficam junto do programa (1.32: sistema\programa\webview2; antes suporte\sistema\webview2).
            AppDomain.CurrentDomain.AssemblyResolve += WebViewHost.Resolve;
#endif
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            bool created;
            using (Mutex mutex = new Mutex(true, "RodoviaStudio_Iniciador_v1", out created))
            {
                Launcher l = new Launcher();
                if (!l.FindRoot())
                {
                    MessageBox.Show("Não encontrei a pasta sistema\\programa do Rodovia Studio.\n\nO arquivo \"Rodovia Studio.exe\" deve ficar na pasta principal do aplicativo (a que tem as pastas projetos, videos e sistema).",
                        "Rodovia Studio", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    return;
                }
                if (!created)
                {
                    // Já aberto: só mostra a janela.
                    if (!l.OpenExisting())
                        MessageBox.Show("O Rodovia Studio já está sendo iniciado. Aguarde alguns segundos.", "Rodovia Studio", MessageBoxButtons.OK, MessageBoxIcon.Information);
                    return;
                }
                if (l.Start()) Application.Run(l);
                l.StopServer();
            }
        }
    }

    class AnimatedLogo : Control
    {
        Bitmap source;
        System.Windows.Forms.Timer timer;
        float angle;
        int frame;
        public AnimatedLogo(Icon icon)
        {
            SetStyle(ControlStyles.SupportsTransparentBackColor, true);
            DoubleBuffered = true;
            BackColor = Color.Transparent;
            source = icon == null ? SystemIcons.Application.ToBitmap() : icon.ToBitmap();
            timer = new System.Windows.Forms.Timer();
            timer.Interval = 45;
            timer.Tick += delegate { angle = (angle + 7f) % 360f; frame++; Invalidate(); };
            timer.Start();
        }
        public void Restart() { angle = 0f; frame = 0; Invalidate(); Update(); timer.Start(); }
        public void Finish()
        {
            timer.Stop(); angle = 0f; frame = 0; Invalidate(); Update();
        }
        protected override void OnPaint(PaintEventArgs e)
        {
            base.OnPaint(e);
            if (source == null) return;
            e.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
            e.Graphics.InterpolationMode = InterpolationMode.HighQualityBicubic;
            float pulse = (float)(0.94 + 0.06 * Math.Sin(frame * 0.14));
            float alpha = (float)(0.58 + 0.42 * (0.5 + 0.5 * Math.Sin(frame * 0.11)));
            float size = Math.Min(Width, Height) * 0.72f * pulse;
            e.Graphics.TranslateTransform(Width / 2f, Height / 2f);
            e.Graphics.RotateTransform(angle);
            ColorMatrix cm = new ColorMatrix(); cm.Matrix33 = alpha;
            using (ImageAttributes ia = new ImageAttributes())
            {
                ia.SetColorMatrix(cm);
                RectangleF dst = new RectangleF(-size / 2f, -size / 2f, size, size);
                e.Graphics.DrawImage(source, Rectangle.Round(dst), 0, 0, source.Width, source.Height, GraphicsUnit.Pixel, ia);
            }
            e.Graphics.ResetTransform();
        }
        protected override void Dispose(bool disposing)
        {
            if (disposing) { if (timer != null) { timer.Stop(); timer.Dispose(); } if (source != null) source.Dispose(); }
            base.Dispose(disposing);
        }
    }

    class Splash : Form
    {
        Label status, version;
        AnimatedLogo logo;
        public Splash(Icon icon, string appVersion)
        {
            Text = "Rodovia Studio";
            FormBorderStyle = FormBorderStyle.FixedDialog;
            StartPosition = FormStartPosition.CenterScreen;
            MaximizeBox = false; MinimizeBox = true;
            ClientSize = new Size(570, 205);
            BackColor = Color.FromArgb(8, 22, 35);
            if (icon != null) Icon = icon;
            logo = new AnimatedLogo(icon); logo.SetBounds(22, 28, 118, 118);
            Label title = new Label();
            title.Text = "Rodovia Studio";
            title.Font = new Font("Segoe UI", 18, FontStyle.Bold);
            title.ForeColor = Color.FromArgb(134, 220, 233);
            title.SetBounds(158, 24, 380, 38);
            version = new Label();
            version.Font = new Font("Segoe UI", 10, FontStyle.Bold);
            version.ForeColor = Color.FromArgb(210, 224, 232);
            version.SetBounds(160, 63, 370, 24);
            Label maker = new Label();
            maker.Text = "Fabricante: Ronaldo Santos";
            maker.Font = new Font("Segoe UI", 9, FontStyle.Regular);
            maker.ForeColor = Color.FromArgb(160, 177, 188);
            maker.SetBounds(160, 87, 370, 22);
            status = new Label();
            status.Font = new Font("Segoe UI", 9.5f);
            status.ForeColor = Color.White;
            status.SetBounds(160, 122, 380, 54);
            Controls.Add(logo); Controls.Add(title); Controls.Add(version); Controls.Add(maker); Controls.Add(status);
            SetVersion(appVersion);
        }
        public void RestartAnimation() { logo.Restart(); }
        public void FinishAnimation()
        {
            if (IsDisposed) return;
            logo.Finish();
            DateTime until = DateTime.UtcNow.AddMilliseconds(180);
            while (!IsDisposed && DateTime.UtcNow < until) { Application.DoEvents(); Thread.Sleep(10); }
        }
        protected override void OnFormClosing(FormClosingEventArgs e)
        {
            logo.Finish(); base.OnFormClosing(e);
        }
        public void SetVersion(string v)
        {
            version.Text = "Versão " + (String.IsNullOrEmpty(v) ? "em verificação" : v);
            version.Refresh();
        }
        public void Status(string text)
        {
            status.Text = text;
            status.Refresh();
            Application.DoEvents();
        }
    }

    class Launcher : ApplicationContext
    {
        public string Root, Sys, Logs, Py;
        Process server;
        int port = 8765;
        NotifyIcon tray;
        Splash splash;
        Icon icon;
        readonly object logLock = new object();
        bool stopping, updateInProgress;
        System.Windows.Forms.Timer updateWatcher;
        string lastUpdateSignature = "";
        string controlToken = "";

        public bool FindRoot()
        {
            // 1.2: organização 1.32 (sistema\programa) e, por compatibilidade, a anterior (suporte\sistema).
            string d = AppDomain.CurrentDomain.BaseDirectory;
            for (int i = 0; i < 4 && d != null; i++)
            {
                string[][] layouts = new string[][] { new string[] { "sistema\\programa", "sistema\\logs" }, new string[] { "suporte\\sistema", "suporte\\logs" } };
                foreach (string[] l in layouts)
                {
                    if (File.Exists(Path.Combine(d, l[0] + "\\run.py")))
                    {
                        Root = d.TrimEnd('\\');
                        Sys = Path.Combine(Root, l[0]);
                        Logs = Path.Combine(Root, l[1]);
                        Directory.CreateDirectory(Logs);
                        Py = Path.Combine(Sys, "runtime\\python.exe");
                        return true;
                    }
                }
                DirectoryInfo p = Directory.GetParent(d.TrimEnd('\\'));
                d = p == null ? null : p.FullName;
            }
            return false;
        }

        string PortFile { get { return Path.Combine(Logs, "porta.txt"); } }
        string Url { get { return "http://127.0.0.1:" + port; } }

        void Log(string file, string text)
        {
            try
            {
                lock (logLock)
                {
                    File.AppendAllText(Path.Combine(Logs, file), DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss ") + text + Environment.NewLine, Encoding.UTF8);
                }
            }
            catch { }
        }

        // ---------------------------------------------------------------- já aberto
        public bool OpenExisting()
        {
            int p;
            if (File.Exists(PortFile) && int.TryParse(File.ReadAllText(PortFile).Trim(), out p)) port = p;
            if (!Healthy()) return false;
            OpenWindow();
            return true;
        }

        string InstalledAppVersion()
        {
            try
            {
                string f = Path.Combine(Sys, "VERSAO.json");
                if (!File.Exists(f)) return "";
                Match m = Regex.Match(File.ReadAllText(f, Encoding.UTF8), "\\\"version\\\"\\s*:\\s*\\\"([^\\\"]+)\\\"");
                return m.Success ? m.Groups[1].Value : "";
            }
            catch { return ""; }
        }

        // ---------------------------------------------------------------- início
        public bool Start()
        {
            try { icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath); } catch { icon = SystemIcons.Application; }
            splash = new Splash(icon, InstalledAppVersion());
            splash.Show();
            try
            {
                if (!Prepare()) return false;
                bool updatedOnStart = ApplyUpdates(false);
                if (updatedOnStart) { FindRoot(); splash.SetVersion(InstalledAppVersion()); Say("Atualização validada e aplicada. Abrindo a nova versão…"); }
                if (!Prepare()) return false;            // uma atualização pode trazer novas dependências
                if (!StartServer()) return false;
                WriteVersionFile();
                splash.FinishAnimation(); splash.Close(); splash = null;
                CreateTray();
                StartUpdateWatcher();
                OpenWindow();
                CheckLauncherVersion();
                MakeShortcut();
                return true;
            }
            catch (Exception ex)
            {
                Log("iniciador.log", "ERRO: " + ex);
                MessageBox.Show("O Rodovia Studio não iniciou:\n\n" + ex.Message + "\n\nDetalhes em sistema\\logs\\iniciador.log.", "Rodovia Studio", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return false;
            }
            finally
            {
                if (splash != null) { splash.Close(); splash = null; }
            }
        }

        void Say(string t) { if (splash != null) splash.Status(t); Log("iniciador.log", t); }

        // Versão e modo de janela do iniciador, mostrados em Ajuda > Sobre.
        void WriteVersionFile()
        {
            string mode = "navegador em modo aplicativo";
#if WEBVIEW2
            if (WebViewHost.Available(Sys)) mode = "janela própria (WebView2)";
#endif
            try { File.WriteAllText(Path.Combine(Logs, "iniciador_versao.txt"), Program.Version + " · " + mode, Encoding.UTF8); } catch { }
        }

        static string Sha256Upper(string file)
        {
            using (SHA256 h = SHA256.Create())
            using (FileStream f = File.OpenRead(file))
            {
                byte[] b = h.ComputeHash(f);
                StringBuilder sb = new StringBuilder();
                foreach (byte x in b) sb.Append(x.ToString("X2"));
                return sb.ToString();
            }
        }

        bool NeedsPreparation()
        {
            if (!File.Exists(Py)) return true;
            string stamp = Path.Combine(Sys, "runtime\\dependencias.ok");
            string req = Path.Combine(Sys, "requirements.txt");
            if (!File.Exists(stamp) || !File.Exists(req)) return true;
            return File.ReadAllText(stamp).Trim().ToUpperInvariant() != Sha256Upper(req);
        }

        // Primeira vez (ou dependências novas): usa o mesmo preparo do ABRIR RODOVIA STUDIO.cmd, numa janela visível.
        bool Prepare()
        {
            if (!NeedsPreparation()) return true;
            Say("Preparando Python, bibliotecas e FFmpeg (primeira vez ou dependências novas).\nAcompanhe na janela que vai abrir.");
            ProcessStartInfo si = new ProcessStartInfo("powershell.exe",
                "-NoProfile -ExecutionPolicy Bypass -File \"" + Path.Combine(Sys, "iniciar.ps1") + "\" -PrepararApenas");
            si.WorkingDirectory = Sys;
            si.UseShellExecute = false;
            Process p = Process.Start(si);
            while (!p.WaitForExit(200)) Application.DoEvents();
            if (p.ExitCode != 0 || NeedsPreparation())
            {
                MessageBox.Show("A preparação não terminou. Confira a mensagem na janela do PowerShell e sistema\\logs\\instalacao.log.\n\nSe a empresa bloqueia downloads ou PowerShell, peça a liberação ao suporte de TI.",
                    "Rodovia Studio", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return false;
            }
            return true;
        }

        // ---------------------------------------------------------------- atualizações
        string PendingUpdateSignature()
        {
            try
            {
                string d = Path.Combine(Root, "atualizacoes");
                if (!Directory.Exists(d)) return "";
                Regex re = new Regex("RodoviaStudio_.*atualiza.*\\.zip$", RegexOptions.IgnoreCase);
                StringBuilder s = new StringBuilder();
                foreach (string f in Directory.GetFiles(d, "*.zip"))
                    if (re.IsMatch(Path.GetFileName(f))) { FileInfo x = new FileInfo(f); s.Append(x.FullName).Append('|').Append(x.Length).Append('|').Append(x.LastWriteTimeUtc.Ticks).Append(';'); }
                return s.ToString();
            }
            catch { return ""; }
        }

        bool HasUpdateZip() { return PendingUpdateSignature().Length > 0; }

        // Usa o atualizador do próprio programa (atualizar.ps1 + atualizador.py). Retorna true se aplicou.
        bool ApplyUpdates(bool interactive)
        {
            if (!HasUpdateZip() || !File.Exists(Py)) { if (interactive) Info("Nenhum ZIP de atualização pendente em \"atualizacoes\"."); return false; }
            Say("Procurando e aplicando atualização…");
            ProcessStartInfo si = new ProcessStartInfo("powershell.exe",
                "-NoProfile -ExecutionPolicy Bypass -File \"" + Path.Combine(Sys, "atualizar.ps1") + "\" -Raiz \"" + Root + "\"");
            si.WorkingDirectory = Root;
            si.UseShellExecute = false;
            si.CreateNoWindow = true;
            si.RedirectStandardOutput = true;
            si.RedirectStandardError = true;
            si.StandardOutputEncoding = Encoding.UTF8;
            Process p = Process.Start(si);
            StringBuilder outText = new StringBuilder();
            p.OutputDataReceived += delegate(object s, DataReceivedEventArgs e) { if (e.Data != null) lock (outText) outText.AppendLine(e.Data); };
            p.ErrorDataReceived += delegate(object s, DataReceivedEventArgs e) { if (e.Data != null) lock (outText) outText.AppendLine(e.Data); };
            p.BeginOutputReadLine(); p.BeginErrorReadLine();
            while (!p.WaitForExit(200)) Application.DoEvents();
            p.WaitForExit();
            string text;
            lock (outText) text = outText.ToString().Trim();
            Log("iniciador.log", "Atualizador: " + text);
            bool applied = text.IndexOf("aplicada", StringComparison.OrdinalIgnoreCase) >= 0 && p.ExitCode == 0;
            if (p.ExitCode != 0)
                MessageBox.Show("A atualização não foi aplicada:\n\n" + Tail(text, 900) + "\n\nO Rodovia Studio continua na versão instalada.", "Rodovia Studio", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            else if (applied) Notify("Atualização aplicada", Tail(text, 250));
            else if (interactive) Info(Tail(text, 500));
            return applied;
        }

        static string Tail(string t, int n) { return t.Length <= n ? t : "…" + t.Substring(t.Length - n); }

        void StartUpdateWatcher()
        {
            if (updateWatcher != null) return;
            updateWatcher = new System.Windows.Forms.Timer();
            updateWatcher.Interval = 5000;
            updateWatcher.Tick += delegate
            {
                if (stopping || updateInProgress) return;
                string sig = PendingUpdateSignature();
                if (File.Exists(Path.Combine(Logs, "solicitar_atualizacao.json")))
                {
                    string request = File.ReadAllText(Path.Combine(Logs, "solicitar_atualizacao.json"));
                    File.Delete(Path.Combine(Logs, "solicitar_atualizacao.json"));
                    if (request.Contains("restaurar")) { RestoreNow(); return; }
                    lastUpdateSignature = "";
                }
                if (sig.Length == 0) { lastUpdateSignature = ""; return; }
                if (sig == lastUpdateSignature) return;
                AutoApplyPendingUpdate();
            };
            updateWatcher.Start();
        }

        bool PrepareUpdateSession()
        {
            if (server == null || server.HasExited) return !Healthy();
            try
            {
                HttpWebRequest ready = (HttpWebRequest)WebRequest.Create(Url + "/api/atualizacao/pronto");
                ready.Timeout = 3000; ready.Proxy = null;
                using (WebResponse response = ready.GetResponse()) { }
#if WEBVIEW2
                if (!WebViewHost.PrepareUpdate()) return false;
#else
                // Sem janela incorporada não há como confirmar o salvamento da página.
                Notify("Atualização adiada", "Use a janela própria do Rodovia Studio para salvar e atualizar com segurança.");
                return false;
#endif
                HttpWebRequest close = (HttpWebRequest)WebRequest.Create(Url + "/api/sessao/encerrar");
                close.Method = "POST"; close.ContentLength = 0; close.Timeout = 5000; close.Proxy = null;
                close.Headers["X-Rodovia-Control"] = controlToken;
                using (WebResponse response = close.GetResponse()) { }
                stopping = true;
                DateTime limit = DateTime.UtcNow.AddSeconds(90);
                while (!server.HasExited && DateTime.UtcNow < limit) { Application.DoEvents(); Thread.Sleep(100); }
                if (!server.HasExited)
                {
                    Log("iniciador.log", "Atualização adiada: servidor não concluiu o encerramento controlado.");
                    stopping = false; return false;
                }
                server.Dispose(); server = null;
                try { File.Delete(PortFile); } catch { }
#if WEBVIEW2
                WebViewHost.CloseAll();
#endif
                stopping = false; return true;
            }
            catch (Exception ex)
            {
                Log("iniciador.log", "Atualização adiada: " + ex.Message);
                stopping = false; return false;
            }
        }

        void RestoreNow()
        {
            if (updateInProgress) return;
            updateInProgress = true;
            try
            {
                if (!PrepareUpdateSession()) return;
                ProcessStartInfo si = new ProcessStartInfo("powershell.exe",
                    "-NoProfile -ExecutionPolicy Bypass -File \"" + Path.Combine(Sys, "atualizar.ps1") + "\" -Raiz \"" + Root + "\" -RestaurarAnterior");
                si.WorkingDirectory = Root; si.UseShellExecute = false;
                Process p = Process.Start(si);
                while (!p.WaitForExit(200)) Application.DoEvents();
                if (p.ExitCode != 0) { if (StartServer()) OpenWindow(); return; }
                Info("Versão anterior restabelecida. Reabra o Rodovia Studio."); Quit();
            }
            catch (Exception ex) { Log("iniciador.log", ex.ToString()); if (server == null && StartServer()) OpenWindow(); }
            finally { updateInProgress = false; }
        }

        void AutoApplyPendingUpdate()
        {
            if (updateInProgress) return;
            updateInProgress = true;
            if (updateWatcher != null) updateWatcher.Stop();
            try
            {
                Notify("Atualização encontrada", "O Rodovia Studio vai encerrar sua sessão, validar o pacote e aplicar a atualização.");
                if (!PrepareUpdateSession()) return;
                lastUpdateSignature = PendingUpdateSignature();
                bool applied = ApplyUpdates(false);
                if (applied)
                {
                    FindRoot();
                    MessageBox.Show("Atualização aplicada com sucesso.\n\nO Rodovia Studio foi encerrado de forma controlada para concluir a troca dos arquivos.\n\nReabra o aplicativo para usar a versão " + InstalledAppVersion() + ".",
                        "Rodovia Studio - Atualização concluída", MessageBoxButtons.OK, MessageBoxIcon.Information);
                    Quit();
                    return;
                }
                if (StartServer()) OpenWindow();
            }
            catch (Exception ex)
            {
                Log("iniciador.log", "Falha na atualização automática: " + ex);
                MessageBox.Show("A atualização automática não foi concluída. A versão instalada foi preservada.\n\n" + ex.Message,
                    "Rodovia Studio", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                try { if (server == null || server.HasExited) { if (StartServer()) OpenWindow(); } } catch { }
            }
            finally
            {
                updateInProgress = false;
                if (!stopping && updateWatcher != null) updateWatcher.Start();
            }
        }

        // ---------------------------------------------------------------- servidor
        public bool StartServer()
        {
            Say("Iniciando o Rodovia Studio…");
            try { File.Delete(PortFile); } catch { }
            ProcessStartInfo si = new ProcessStartInfo(Py, "-X utf8 \"" + Path.Combine(Sys, "run.py") + "\"");
            si.WorkingDirectory = Sys;
            si.UseShellExecute = false;
            si.CreateNoWindow = true;
            si.RedirectStandardOutput = true;
            si.RedirectStandardError = true;
            si.StandardOutputEncoding = Encoding.UTF8;
            si.StandardErrorEncoding = Encoding.UTF8;
            controlToken = Guid.NewGuid().ToString("N");
            si.EnvironmentVariables["RODOVIA_CONTROL_TOKEN"] = controlToken;
            si.EnvironmentVariables["RODOVIA_NO_BROWSER"] = "1";
            si.EnvironmentVariables["RODOVIA_PORT_FILE"] = PortFile;
            si.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8";
            server = Process.Start(si);
            server.OutputDataReceived += delegate(object s, DataReceivedEventArgs e) { if (e.Data != null) Log("servidor.log", e.Data); };
            server.ErrorDataReceived += delegate(object s, DataReceivedEventArgs e) { if (e.Data != null) Log("servidor.log", e.Data); };
            server.BeginOutputReadLine(); server.BeginErrorReadLine();
            DateTime limit = DateTime.Now.AddSeconds(120);
            while (DateTime.Now < limit)
            {
                Application.DoEvents();
                int p;
                if (File.Exists(PortFile))
                {
                    try { if (int.TryParse(File.ReadAllText(PortFile).Trim(), out p)) port = p; } catch { }
                    if (Healthy()) return true;
                }
                if (server.HasExited)
                {
                    // run.py encerra com 0 quando outro Rodovia Studio já está aberto: usa aquele.
                    if (server.ExitCode == 0 && File.Exists(PortFile) && Healthy()) { server = null; return true; }
                    MessageBox.Show("O servidor do Rodovia Studio encerrou ao iniciar.\n\nVeja sistema\\logs\\servidor.log e sistema\\programa\\servidor_erro.log.",
                        "Rodovia Studio", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    return false;
                }
                Thread.Sleep(150);
            }
            MessageBox.Show("O Rodovia Studio demorou demais para iniciar (2 min). Veja sistema\\logs\\servidor.log.", "Rodovia Studio", MessageBoxButtons.OK, MessageBoxIcon.Error);
            StopServer();
            return false;
        }

        bool Healthy()
        {
            try
            {
                HttpWebRequest r = (HttpWebRequest)WebRequest.Create(Url + "/api/health");
                r.Timeout = 1500; r.Proxy = null;
                using (HttpWebResponse resp = (HttpWebResponse)r.GetResponse())
                using (StreamReader sr = new StreamReader(resp.GetResponseStream()))
                    return sr.ReadToEnd().Contains("ok");
            }
            catch { return false; }
        }

        public void StopServer()
        {
            stopping = true;
            if (server == null) return;
            try
            {
                if (!server.HasExited)
                {
                    // Encerra também os processos auxiliares (geração de vídeo, prévia).
                    ProcessStartInfo k = new ProcessStartInfo("taskkill", "/PID " + server.Id + " /T /F");
                    k.CreateNoWindow = true; k.UseShellExecute = false;
                    Process kp = Process.Start(k); kp.WaitForExit(10000);
                }
            }
            catch { }
            server = null;
            try { File.Delete(PortFile); } catch { }
        }

        // ---------------------------------------------------------------- janela
        public void OpenWindow()
        {
#if WEBVIEW2
            // 1.1: janela própria do Windows (WebView2), sem navegador nem barra de endereço.
            if (WebViewHost.Available(Sys))
            {
                try { if (WebViewHost.Show(Url, Sys, Logs, icon)) return; }
                catch (Exception ex) { Log("iniciador.log", "WebView2 indisponível: " + ex.Message); }
            }
#endif
            string[] browsers = new string[] {
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86), "Microsoft\\Edge\\Application\\msedge.exe"),
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), "Microsoft\\Edge\\Application\\msedge.exe"),
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), "Google\\Chrome\\Application\\chrome.exe"),
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86), "Google\\Chrome\\Application\\chrome.exe"),
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Google\\Chrome\\Application\\chrome.exe") };
            foreach (string b in browsers)
            {
                if (!File.Exists(b)) continue;
                try { Process.Start(b, "--app=" + Url + " --new-window"); return; } catch { }
            }
            try { Process.Start(Url); } catch (Exception ex) { Info("Abra no navegador: " + Url + "\n\n" + ex.Message); }
        }

        // ---------------------------------------------------------------- bandeja
        void CreateTray()
        {
            tray = new NotifyIcon();
            tray.Icon = icon;
            tray.Text = "Rodovia Studio";
            ContextMenuStrip m = new ContextMenuStrip();
            m.Items.Add("Abrir Rodovia Studio", null, delegate { OpenWindow(); });
            m.Items.Add("Abrir pasta de projetos", null, delegate { OpenFolder(Path.Combine(Root, "projetos")); });
            m.Items.Add("Abrir pasta de vídeos", null, delegate { OpenFolder(Path.Combine(Root, "videos")); });
            m.Items.Add("Procurar e aplicar atualização", null, delegate { UpdateNow(); });
            m.Items.Add("Reiniciar o aplicativo", null, delegate { Restart(); });
            m.Items.Add("Ver registro (logs)", null, delegate { OpenFolder(Logs); });
            m.Items.Add(new ToolStripSeparator());
            m.Items.Add("Encerrar o Rodovia Studio", null, delegate { Quit(); });
            tray.ContextMenuStrip = m;
            tray.DoubleClick += delegate { OpenWindow(); };
            tray.Visible = true;
            Notify("Rodovia Studio aberto", "O aplicativo fica no ícone perto do relógio. Clique com o botão direito para atualizar ou encerrar.");
            System.Windows.Forms.Timer t = new System.Windows.Forms.Timer();
            t.Interval = 5000;
            t.Tick += delegate
            {
                if (stopping || updateInProgress || server == null) return;
                if (server.HasExited)
                {
                    t.Stop();
                    Log("iniciador.log", "Servidor encerrou com código " + server.ExitCode);
                    if (MessageBox.Show("O servidor do Rodovia Studio encerrou. Reiniciar?", "Rodovia Studio", MessageBoxButtons.YesNo, MessageBoxIcon.Warning) == DialogResult.Yes)
                    { if (StartServer()) { OpenWindow(); t.Start(); } }
                    else Quit();
                }
            };
            t.Start();
        }

        void OpenFolder(string d) { try { Directory.CreateDirectory(d); Process.Start("explorer.exe", "\"" + d + "\""); } catch { } }

        void Notify(string title, string text)
        {
            if (tray == null) return;
            try { tray.ShowBalloonTip(6000, title, text.Length > 250 ? text.Substring(0, 250) : text, ToolTipIcon.Info); } catch { }
        }

        static void Info(string text) { MessageBox.Show(text, "Rodovia Studio", MessageBoxButtons.OK, MessageBoxIcon.Information); }

        void UpdateNow()
        {
            if (updateInProgress) return;
            if (!HasUpdateZip()) { Info("Nenhum ZIP de atualização pendente em atualizacoes/."); return; }
            if (MessageBox.Show("Salvar o projeto e aplicar a atualização? Tarefas em andamento adiam a operação.", "Rodovia Studio", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return;
            AutoApplyPendingUpdate();
        }

        void Restart()
        {
            StopServer(); stopping = false;
            if (StartServer()) OpenWindow(); else Quit();
        }

        void Quit()
        {
            stopping = true;
            if (updateWatcher != null) { updateWatcher.Stop(); updateWatcher.Dispose(); updateWatcher = null; }
#if WEBVIEW2
            WebViewHost.CloseAll();
#endif
            StopServer();
            if (tray != null) { tray.Visible = false; tray.Dispose(); tray = null; }
            ExitThread();
        }

        // Se uma atualização trouxe um iniciador mais novo, avisa para recompilar (o .exe em uso não se troca sozinho).
        void CheckLauncherVersion()
        {
            try
            {
                string src = Path.Combine(Sys, "iniciador\\RodoviaStudio.cs");
                if (!File.Exists(src)) return;
                Match m = Regex.Match(File.ReadAllText(src), "Version\\s*=\\s*\"([^\"]+)\"");
                if (m.Success && m.Groups[1].Value != Program.Version)
                    Notify("Nova versão do iniciador", "Feche o Rodovia Studio e execute \"COMPILAR INICIADOR.cmd\" para atualizar o .exe (" + Program.Version + " → " + m.Groups[1].Value + ").");
            }
            catch { }
        }

        // Atalho "Rodovia Studio" na Área de Trabalho apontando para o .exe (uma vez).
        void MakeShortcut()
        {
            string flag = Path.Combine(Logs, "atalho_exe.ok");
            if (File.Exists(flag)) return;
            try
            {
                Type t = Type.GetTypeFromProgID("WScript.Shell");
                object sh = Activator.CreateInstance(t);
                string lnkPath = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory), "Rodovia Studio.lnk");
                object lnk = t.InvokeMember("CreateShortcut", BindingFlags.InvokeMethod, null, sh, new object[] { lnkPath });
                Type lt = lnk.GetType();
                lt.InvokeMember("TargetPath", BindingFlags.SetProperty, null, lnk, new object[] { Application.ExecutablePath });
                lt.InvokeMember("WorkingDirectory", BindingFlags.SetProperty, null, lnk, new object[] { Root });
                lt.InvokeMember("IconLocation", BindingFlags.SetProperty, null, lnk, new object[] { Application.ExecutablePath + ",0" });
                lt.InvokeMember("Description", BindingFlags.SetProperty, null, lnk, new object[] { "Rodovia Studio" });
                lt.InvokeMember("Save", BindingFlags.InvokeMethod, null, lnk, null);
                File.WriteAllText(flag, "ok");
            }
            catch (Exception ex) { Log("iniciador.log", "Atalho não criado: " + ex.Message); }
        }
    }

#if WEBVIEW2
    // ------------------------------------------------------------------ janela própria (WebView2)
    // Compilado só quando COMPILAR INICIADOR.cmd encontra as DLLs do WebView2 (pacote Microsoft.Web.WebView2).
    // O "motor" é o Microsoft Edge WebView2 Runtime, já presente no Windows 10/11 atualizados.
    static class WebViewHost
    {
        static string dir;
        static AppWindow window;   // acesso ao salvamento controlado da janela incorporada

        public static Assembly Resolve(object sender, ResolveEventArgs args)
        {
            try
            {
                string name = new AssemblyName(args.Name).Name + ".dll";
                string d = dir;
                if (d == null)
                {
                    string b = AppDomain.CurrentDomain.BaseDirectory;
                    d = Path.Combine(b, "sistema\\programa\\webview2");
                    if (!Directory.Exists(d)) d = Path.Combine(b, "suporte\\sistema\\webview2");
                }
                string f = Path.Combine(d, name);
                if (File.Exists(f)) return Assembly.LoadFrom(f);
            }
            catch { }
            return null;
        }

        public static bool Available(string sys)
        {
            dir = Path.Combine(sys, "webview2");
            return File.Exists(Path.Combine(dir, "Microsoft.Web.WebView2.WinForms.dll")) && File.Exists(Path.Combine(dir, "Microsoft.Web.WebView2.Core.dll")) && File.Exists(Path.Combine(dir, "WebView2Loader.dll"));
        }

        [MethodImpl(MethodImplOptions.NoInlining)]
        public static bool Show(string url, string sys, string logs, Icon icon)
        {
            if (window != null && !window.IsDisposed)
            {
                if (window.WindowState == FormWindowState.Minimized) window.WindowState = FormWindowState.Normal;
                window.Show(); window.Activate();
                return true;
            }
            window = new AppWindow(url, Path.Combine(sys, "webview2"), Path.Combine(sys, "webview2_dados"), Path.Combine(logs, "janela.txt"), icon);
            window.Show();
            return true;
        }

        [MethodImpl(MethodImplOptions.NoInlining)]
        public static bool PrepareUpdate()
        {
            return window != null && !window.IsDisposed && window.PrepareUpdate();
        }

        [MethodImpl(MethodImplOptions.NoInlining)]
        public static void CloseAll()
        {
            if (window != null && !window.IsDisposed) window.Close();
            window = null;
        }
    }

    class AppWindow : Form
    {
        Microsoft.Web.WebView2.WinForms.WebView2 web;
        string url, place;
        static bool loaderSet;

        public AppWindow(string url, string dllDir, string dataDir, string placeFile, Icon icon)
        {
            this.url = url; place = placeFile;
            Text = "Rodovia Studio";
            if (icon != null) Icon = icon;
            StartPosition = FormStartPosition.Manual;
            Rectangle wa = Screen.PrimaryScreen.WorkingArea;
            Bounds = new Rectangle(wa.X + 40, wa.Y + 30, Math.Min(1600, wa.Width - 80), Math.Min(1000, wa.Height - 60));
            WindowState = FormWindowState.Maximized;
            RestorePlace();
            BackColor = Color.FromArgb(11, 20, 32);
            if (dllDir != null && !loaderSet) { Microsoft.Web.WebView2.Core.CoreWebView2Environment.SetLoaderDllFolderPath(dllDir); loaderSet = true; }
            web = new Microsoft.Web.WebView2.WinForms.WebView2();
            web.Dock = DockStyle.Fill;
            Controls.Add(web);
            Directory.CreateDirectory(dataDir);
            Init(dataDir);
            FormClosing += delegate(object s, FormClosingEventArgs e) { SavePlace(); };
        }

        async void Init(string dataDir)
        {
            try
            {
                Microsoft.Web.WebView2.Core.CoreWebView2Environment env = await Microsoft.Web.WebView2.Core.CoreWebView2Environment.CreateAsync(null, dataDir);
                await web.EnsureCoreWebView2Async(env);
                web.CoreWebView2.Settings.IsStatusBarEnabled = false;
                web.CoreWebView2.DocumentTitleChanged += delegate { string t = web.CoreWebView2.DocumentTitle; Text = string.IsNullOrEmpty(t) ? "Rodovia Studio" : t; };
                web.CoreWebView2.NewWindowRequested += delegate(object s, Microsoft.Web.WebView2.Core.CoreWebView2NewWindowRequestedEventArgs e)
                {
                    // "Duas janelas": abre outra janela própria com a mesma sessão.
                    if (e.Uri.StartsWith(url, StringComparison.OrdinalIgnoreCase))
                    {
                        e.Handled = true;
                        AppWindow w = new AppWindow(e.Uri, null, dataDir, place + ".2", Icon);
                        w.Show();
                    }
                };
                web.Source = new Uri(url);
            }
            catch (Exception ex)
            {
                MessageBox.Show("Não foi possível abrir a janela própria (WebView2): " + ex.Message + "\n\nO Rodovia Studio vai abrir no navegador.", "Rodovia Studio", MessageBoxButtons.OK, MessageBoxIcon.Information);
                try { Process.Start(url); } catch { }
                Close();
            }
        }

        public bool PrepareUpdate()
        {
            if (web == null || web.CoreWebView2 == null) return false;
            var begin = web.CoreWebView2.ExecuteScriptAsync("window.__rodoviaUpdateReady=null; Promise.resolve().then(()=>window.rodoviaPrepararAtualizacao()).then(v=>window.__rodoviaUpdateReady=v===true).catch(()=>window.__rodoviaUpdateReady=false);");
            DateTime limit = DateTime.UtcNow.AddSeconds(30);
            while (!begin.IsCompleted && DateTime.UtcNow < limit) { Application.DoEvents(); Thread.Sleep(20); }
            if (!begin.IsCompleted || begin.IsFaulted) return false;
            while (DateTime.UtcNow < limit)
            {
                var result = web.CoreWebView2.ExecuteScriptAsync("window.__rodoviaUpdateReady");
                while (!result.IsCompleted && DateTime.UtcNow < limit) { Application.DoEvents(); Thread.Sleep(20); }
                if (!result.IsCompleted || result.IsFaulted) return false;
                if (result.Result == "true") return true;
                if (result.Result == "false") return false;
                Application.DoEvents(); Thread.Sleep(50);
            }
            return false;
        }

        void RestorePlace()
        {
            try
            {
                if (place == null || !File.Exists(place)) return;
                string[] v = File.ReadAllText(place).Split(';');
                Rectangle r = new Rectangle(int.Parse(v[0]), int.Parse(v[1]), int.Parse(v[2]), int.Parse(v[3]));
                bool visible = false;
                foreach (Screen sc in Screen.AllScreens) if (sc.WorkingArea.IntersectsWith(r)) visible = true;
                if (visible && r.Width > 400 && r.Height > 300) { WindowState = FormWindowState.Normal; Bounds = r; }
                if (v.Length > 4 && v[4] == "max") WindowState = FormWindowState.Maximized;
            }
            catch { }
        }

        void SavePlace()
        {
            try
            {
                if (place == null) return;
                Rectangle r = WindowState == FormWindowState.Normal ? Bounds : RestoreBounds;
                File.WriteAllText(place, r.X + ";" + r.Y + ";" + r.Width + ";" + r.Height + ";" + (WindowState == FormWindowState.Maximized ? "max" : "normal"));
            }
            catch { }
        }
    }
#endif
}
