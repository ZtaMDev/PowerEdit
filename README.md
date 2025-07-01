# PowerEdit <img src="https://github.com/user-attachments/assets/cab68082-bd3e-494e-9781-734a50397a1e" alt="Pe" width="30"/> 

## Documentation
- Power Edit now have [**Documentation**](https://ztamdev.github.io/PowerEdit/)
---

I’m thrilled to share **PowerEdit**, my first open-source code editor project. After a month of intense development, it’s matured into something I’m proud of. Here on GitHub, you can:

- **Download**, **use**, and **explore** the editor freely  
- **Contribute** improvements and new features  
- **Report** any bugs or quirks you encounter  


---
<table>
  <tr>
    <td>
      <img src="https://github.com/user-attachments/assets/6d36cdc8-a05d-4f0d-9ed3-a39179e6b5d0" width="800"/>
    </td>
    <td>
      <img src="https://github.com/user-attachments/assets/d8a7ff01-c099-4947-829d-0e639b8da249" alt="Captura 2" width="400"/>
      <img src="https://github.com/user-attachments/assets/71b8854e-5c8c-4453-b0f9-939695861504" width="400"/>
    </td>
  </tr>
</table>

---

## 📥 How to download PowerEdit

1. Go to the section [**Releases**](https://github.com/ztamdev/PowerEdit/releases) of this repository.  
2. Download the latest version for your operating system (Windows, macOS, Linux).
3. Run the .exe installer:
   ```bash
   PowerEdit-Setup-v1.0.0.exe  # Windows
   ```


---
## Lastest Release Notes:

## Added Features

### ✅ New EditorAPI
A powerful and easy-to-use **EditorAPI** has been added. This API allows the creation of editor extensions with great simplicity.  
The API is included in the project files here: [EditorAPI File](https://github.com/ZtaMDev/PowerEdit/blob/main/editor_api.py)  
It allows extensions to:
- Modify editor behaviors
- Add custom menus and buttons
- Access parameters from the current editor session
- And much more...

Full documentation will be available soon at:  
[https://ztamdev.github.io/PowerEdit/](https://ztamdev.github.io/PowerEdit/)

---

### New Extensions Manager Menu
A brand-new **Extensions Manager** menu is now available. It allows you to:
- Install and uninstall extensions either locally (with `.ext` extension bundles)
- Or from the official Power Edit Extensions Repository:  
  [https://github.com/ZtaMDev/poweredit-extensions](https://github.com/ZtaMDev/poweredit-extensions)

You can now also **view detailed information** about any installed extension directly from the manager.

---

### New Extension: Extension Creator
This new tool makes it incredibly easy to create extensions through a graphical interface.

Features include:
- Set a title and description for your extension
- Automatically generate an `.ext` extension bundle
- Display important metadata about the extension
- If your extension requires additional Python modules, simply include a `requirements.txt` in your extension folder.  
  These modules will be automatically installed in the embedded Python environment during installation.

---


## 🔧 How You Can Help

1. **Star ⭐** the repo to show support  
2. **Open issues** for any bugs or UX problems  
3. **Submit pull requests** with enhancements or fixes  
4. **Suggest integrations** (e.g. AI-powered code completion)  
5. **Share** PowerEdit with friends and classmates

 ## 🙌 Want to Contribute?

We welcome contributions! Please read our [Contributing Guide](https://github.com/ZtaMDev/PowerEdit/blob/main/CONTRIBUTING.md) before making a pull request.

---

## 📋Start Key Features

> Note If you will to know the last updates and features go to the [**Releases**](https://github.com/ztamdev/PowerEdit/releases) page.

- **Tabbed editor** with syntax highlighting  
- **Custom themes** loaded from `.theme` files  
- **Syntax highlighting extension packs** via `.extend` files
- **Integrated live preview** for web developers
- **Minimap** of the code for a short preview of the file
- **Integrated console** powered by `pyte` for real-time output  
- **Update Manager** fetches & installs new releases automatically  
- **Source Downloader** pulls the latest code ZIP right from GitHub  

---

## 🌟 What’s Next?

- **Indentation & formatting fixes**  
- **Plugin/extension API** (think VS Code-style)  
- **Built-in AI assistants** (free!)  
- **Cross-platform installers** (Windows, macOS, Linux)  

Thank you for joining this journey—let’s make PowerEdit even better together! 🎉  

> **Hola!**  
> Estoy muy orgulloso de lanzar este proyecto, pues lo llevo desarrollando 1 mes y ha avanzado muchísimo en mi opinión.  
> Por eso lo subo a GitHub para que todos puedan usarlo. El editor funciona bastante bien y quiero que me ayuden a mejorarlo lo más posible,  
> ya que es mi primer proyecto open source de este tipo y quiero llevarlo al siguiente nivel.  
>  
> Cuenta con un **Update Manager** que actualizará el editor a la última versión,  
> y un **gestor de descargas de código fuente**: desde la sección **Help → Download Source** puedes descargar todo el código para su edición.  
> (Recomiendo usar VS Code en lugar de PowerEdit para editar, pues aún hay algunos conflictos de indentación.)  
>  
> Con vuestra ayuda espero resolver esos detalles, añadir nuevas funcionalidades y, en breve, incorporar IA… ¡de forma completamente gratuita!  
